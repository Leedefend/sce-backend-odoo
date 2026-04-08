#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def _post(self, path: str, payload: dict, headers: dict | None = None):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            return int(response.status), body

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        status, body = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": 1,
            },
        )
        if status != 200:
            return 0
        result = body.get("result") if isinstance(body, dict) else {}
        return int((result or {}).get("uid") or 0)

    def call_kw(self, model: str, method: str, args: list, kwargs: dict | None = None):
        self._id += 1
        status, body = self._post(
            "/web/dataset/call_kw",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args,
                    "kwargs": kwargs or {},
                },
                "id": self._id,
            },
        )
        if status != 200:
            raise RuntimeError(f"call_kw status={status} model={model} method={method}")
        if body.get("error"):
            message = ((body.get("error") or {}).get("data") or {}).get("message") or str(body.get("error"))
            raise RuntimeError(f"call_kw error model={model} method={method}: {message}")
        return body.get("result")

    def intent(self, intent: str, params: dict):
        return self._post(
            "/api/v1/intent",
            {"intent": intent, "params": params},
            headers={"X-Anonymous-Intent": "1"},
        )


def _extract_role_entries(payload: dict) -> list[dict]:
    data = payload.get("data") if isinstance(payload, dict) else {}
    if not isinstance(data, dict):
        return []
    direct_rows = data.get("role_entries")
    if isinstance(direct_rows, list):
        return direct_rows
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    module_facts = ext_facts.get("smart_construction_core") if isinstance(ext_facts.get("smart_construction_core"), dict) else {}
    rows = module_facts.get("role_entries")
    return rows if isinstance(rows, list) else []


def _to_id(value) -> int:
    if isinstance(value, int):
        return int(value)
    if isinstance(value, list) and value:
        head = value[0]
        if isinstance(head, int):
            return int(head)
    try:
        return int(value or 0)
    except Exception:
        return 0


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    admin_login = _env("ADMIN_LOGIN", "admin")
    admin_password = _env("ADMIN_PASSWORD", "admin")

    session = OdooSession(base_url)
    uid = session.authenticate(db_name, admin_login, admin_password)
    if uid <= 0:
        raise SystemExit("[native_business_admin_config_role_entry_intent_parity_verify] FAIL admin auth failed")

    suffix = str(int(time.time()))
    create_vals = [
        {
            "type": "role_entry",
            "code": f"project.list.{suffix}",
            "name": "项目列表入口",
            "scope_type": "role",
            "scope_ref": "project_manager",
            "value_json": {"entry_key": f"project.list.{suffix}", "entry_type": "menu", "is_enabled": True},
        },
        {
            "type": "role_entry",
            "code": f"payment.request.{suffix}",
            "name": "付款入口",
            "scope_type": "role",
            "scope_ref": "finance",
            "value_json": {"entry_key": f"payment.request.{suffix}", "entry_type": "menu", "is_enabled": True},
        },
    ]

    created_ids: list[int] = []
    original_extension_modules = ""
    try:
        original_extension_modules = str(
            session.call_kw("ir.config_parameter", "get_param", ["sc.core.extension_modules"], {}) or ""
        )
        enabled_modules = [item.strip() for item in original_extension_modules.split(",") if item.strip()]
        if "smart_construction_core" not in enabled_modules:
            enabled_modules.append("smart_construction_core")
            session.call_kw(
                "ir.config_parameter",
                "set_param",
                ["sc.core.extension_modules", ",".join(enabled_modules)],
                {},
            )

        for vals in create_vals:
            rec_id = _to_id(session.call_kw("sc.dictionary", "create", [[vals]], {}))
            if rec_id <= 0:
                raise SystemExit(
                    "[native_business_admin_config_role_entry_intent_parity_verify] FAIL create role_entry failed"
                )
            created_ids.append(rec_id)

        status, body = session.intent("system.init", {"contract_mode": "user"})
        if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
            raise SystemExit(
                "[native_business_admin_config_role_entry_intent_parity_verify] FAIL "
                f"system.init not ok status={status}"
            )

        role_entries = _extract_role_entries(body)
        if not role_entries:
            raise SystemExit(
                "[native_business_admin_config_role_entry_intent_parity_verify] FAIL role_entries missing in system.init ext_facts"
            )

        runtime_rows = session.call_kw(
            "sc.dictionary",
            "search_read",
            [[("id", "in", created_ids)]],
            {"fields": ["code", "scope_ref"], "order": "id asc"},
        )
        expected = {(str(row.get("scope_ref") or ""), str(row.get("code") or "")) for row in (runtime_rows or [])}

        actual: set[tuple[str, str]] = set()
        for item in role_entries:
            if not isinstance(item, dict):
                continue
            role_code = str(item.get("role_code") or "")
            entries = item.get("entries") if isinstance(item.get("entries"), list) else []
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                actual.add((role_code, str(entry.get("entry_key") or "")))

        missing = sorted([pair for pair in expected if pair not in actual])
        if missing:
            raise SystemExit(
                "[native_business_admin_config_role_entry_intent_parity_verify] FAIL "
                f"missing pairs in contract={missing}"
            )

        print(
            "[native_business_admin_config_role_entry_intent_parity_verify] PASS "
            f"uid={uid} expected_pairs={len(expected)} role_groups={len(role_entries)}"
        )
    finally:
        session.call_kw(
            "ir.config_parameter",
            "set_param",
            ["sc.core.extension_modules", original_extension_modules],
            {},
        )
        if created_ids:
            session.call_kw("sc.dictionary", "unlink", [created_ids], {})


if __name__ == "__main__":
    main()
