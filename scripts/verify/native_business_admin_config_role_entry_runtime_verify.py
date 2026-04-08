#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class SessionClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post(self, path: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
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
        status, body = self.post(
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
        status, body = self.post(
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
                "id": 99,
            },
        )
        if status != 200:
            raise RuntimeError(f"call_kw status={status} model={model} method={method}")
        if body.get("error"):
            raise RuntimeError(str(body.get("error")))
        return body.get("result")


def _extract_role_entries(body: dict) -> list[dict]:
    data = body.get("data") if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        return []
    direct_rows = data.get("role_entries")
    if isinstance(direct_rows, list):
        return direct_rows
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    module_facts = ext_facts.get("smart_construction_core") if isinstance(ext_facts.get("smart_construction_core"), dict) else {}
    role_entries = module_facts.get("role_entries")
    return role_entries if isinstance(role_entries, list) else []


def _validate_shape(role: str, rows: list[dict], failures: list[str], details: list[str]) -> None:
    for item in rows:
        if not isinstance(item, dict):
            failures.append(f"{role}: role-entry group not dict")
            continue
        role_code = str(item.get("role_code") or "")
        entries = item.get("entries")
        if not role_code:
            failures.append(f"{role}: empty role_code")
        if not isinstance(entries, list):
            failures.append(f"{role}: entries not list role_code={role_code}")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                failures.append(f"{role}: entry not dict role_code={role_code}")
                continue
            if not str(entry.get("entry_key") or ""):
                failures.append(f"{role}: empty entry_key role_code={role_code}")
            if not str(entry.get("entry_type") or ""):
                failures.append(f"{role}: empty entry_type role_code={role_code}")
    details.append(f"{role}:groups={len(rows)}")


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    roles = [
        ("admin", "admin", ["admin"]),
        ("pm", "sc_fx_pm", ["demo", "prod_like", "admin"]),
        ("finance", "sc_fx_finance", ["demo", "prod_like", "admin"]),
        ("outsider", outsider_login, ["demo", "prod_like", "admin"]),
    ]

    failures: list[str] = []
    details: list[str] = []

    admin_client = SessionClient(base_url)
    admin_uid = admin_client.authenticate(db_name, "admin", "admin")
    original_extension_modules = ""
    if admin_uid > 0:
        original_extension_modules = str(
            admin_client.call_kw("ir.config_parameter", "get_param", ["sc.core.extension_modules"], {}) or ""
        )
        enabled_modules = [item.strip() for item in original_extension_modules.split(",") if item.strip()]
        if "smart_construction_core" not in enabled_modules:
            enabled_modules.append("smart_construction_core")
            admin_client.call_kw(
                "ir.config_parameter",
                "set_param",
                ["sc.core.extension_modules", ",".join(enabled_modules)],
                {},
            )

    try:
        for role, login, passwords in roles:
            client = None
            uid = 0
            for password in passwords:
                probe = SessionClient(base_url)
                uid = probe.authenticate(db_name, login, password)
                if uid > 0:
                    client = probe
                    break
            if not client:
                failures.append(f"{role}: auth failed")
                continue

            status, body = client.post(
                "/api/v1/intent",
                {"intent": "system.init", "params": {"contract_mode": "user"}},
                headers={"X-Anonymous-Intent": "1"},
            )
            if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
                failures.append(f"{role}: system.init failed status={status}")
                continue

            role_entries = _extract_role_entries(body)
            if not role_entries:
                failures.append(f"{role}: role_entries missing")
                continue

            _validate_shape(role, role_entries, failures, details)
            details.append(f"{role}:uid={uid}")
    finally:
        if admin_uid > 0:
            admin_client.call_kw(
                "ir.config_parameter",
                "set_param",
                ["sc.core.extension_modules", original_extension_modules],
                {},
            )

    if failures:
        raise SystemExit("[native_business_admin_config_role_entry_runtime_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_role_entry_runtime_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
