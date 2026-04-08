#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from datetime import date
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._id = 0
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar())
        )

    def _post(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("error"):
            raise RuntimeError(json.dumps(body["error"], ensure_ascii=False))
        return body.get("result")

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        self._id += 1
        result = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": self._id,
            },
        )
        uid = int(result.get("uid") or 0)
        if uid <= 0:
            raise RuntimeError(f"auth failed: {login}")
        return uid

    def call_kw(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None):
        self._id += 1
        return self._post(
            f"/web/dataset/call_kw/{model}/{method}",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                },
                "id": self._id,
            },
        )


def _to_id(value) -> int:
    if isinstance(value, list):
        if not value:
            return 0
        return int(value[0] or 0)
    return int(value or 0)


def _find_config_admin_login(admin: OdooSession, fallback_login: str) -> str:
    group_rows = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "smart_construction_core"), ("name", "=", "group_sc_cap_config_admin")]],
        {"fields": ["res_id"], "limit": 1},
    )
    if not group_rows:
        return fallback_login
    group_id = int(group_rows[0]["res_id"])
    users = admin.call_kw(
        "res.users",
        "search_read",
        [[("groups_id", "in", [group_id]), ("active", "=", True)]],
        {"fields": ["login"], "limit": 1},
    )
    if not users:
        return fallback_login
    return str(users[0].get("login") or fallback_login).strip()


def _assert_menu_action_runtime(admin: OdooSession, failures: list[str], details: list[str]) -> None:
    pairs = [
        ("action_sc_config_system_param", "menu_sc_config_system_param"),
        ("action_sc_config_role_entry", "menu_sc_config_role_entry"),
        ("action_sc_config_home_block", "menu_sc_config_home_block"),
    ]
    for action_xmlid, menu_xmlid in pairs:
        action_ref = admin.call_kw(
            "ir.model.data",
            "search_read",
            [[("module", "=", "smart_construction_core"), ("name", "=", action_xmlid)]],
            {"fields": ["res_id"], "limit": 1},
        )
        menu_ref = admin.call_kw(
            "ir.model.data",
            "search_read",
            [[("module", "=", "smart_construction_core"), ("name", "=", menu_xmlid)]],
            {"fields": ["res_id"], "limit": 1},
        )
        if not action_ref:
            failures.append(f"missing action xmlid runtime: {action_xmlid}")
            continue
        if not menu_ref:
            failures.append(f"missing menu xmlid runtime: {menu_xmlid}")
            continue
    if not failures:
        details.append("runtime menu/action xmlid ok")


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_prod_sim")
    admin_login = _env("ADMIN_LOGIN", "admin")
    admin_password = _env("ADMIN_PASSWORD", "admin")
    config_admin_login = _env("ROLE_CONFIG_ADMIN_LOGIN", "")
    config_admin_password = _env("ROLE_CONFIG_ADMIN_PASSWORD", _env("ADMIN_PASSWORD", "admin"))

    failures: list[str] = []
    details: list[str] = []

    admin = OdooSession(base_url)
    try:
        admin.authenticate(db_name, admin_login, admin_password)
    except Exception as error:
        raise SystemExit(
            "[native_business_admin_config_center_runtime_clickpath_verify] FAIL "
            f"admin login unreachable base_url={base_url} db={db_name} error={error}"
        )

    if not config_admin_login:
        config_admin_login = _find_config_admin_login(admin, admin_login)

    role_session = OdooSession(base_url)
    try:
        role_uid = role_session.authenticate(db_name, config_admin_login, config_admin_password)
    except Exception as error:
        raise SystemExit(
            "[native_business_admin_config_center_runtime_clickpath_verify] FAIL "
            f"config-admin login failed login={config_admin_login} db={db_name} error={error}"
        )

    suffix = f"{date.today().strftime('%Y%m%d')}-{int(time.time())}"
    silent_context = {
        "tracking_disable": True,
        "mail_create_nosubscribe": True,
        "mail_auto_subscribe_no_notify": True,
    }

    records = [
        ("system_param", f"CFG-SYS-{suffix}", "系统参数配置样本"),
        ("role_entry", f"CFG-ROLE-{suffix}", "角色入口配置样本"),
        ("home_block", f"CFG-HOME-{suffix}", "首页区块配置样本"),
    ]

    created_ids: list[int] = []
    for cfg_type, code, name in records:
        rec_id = _to_id(
            role_session.call_kw(
                "sc.dictionary",
                "create",
                [[{
                    "type": cfg_type,
                    "code": code,
                    "name": name,
                    "scope_type": "global",
                    "scope_ref": "",
                    "value_text": "initial",
                    "value_json": {"enabled": True, "source": "runtime_verify"},
                    "note": "runtime click-path verify",
                }]],
                {"context": silent_context},
            )
        )
        if rec_id <= 0:
            failures.append(f"create failed type={cfg_type}")
            continue
        created_ids.append(rec_id)

        role_session.call_kw(
            "sc.dictionary",
            "write",
            [[rec_id], {"value_text": "edited", "note": "runtime click-path edited"}],
            {"context": silent_context},
        )

        row = role_session.call_kw(
            "sc.dictionary",
            "read",
            [[rec_id], ["type", "code", "value_text", "scope_type", "note", "create_uid"]],
            {},
        )[0]
        if str(row.get("type") or "") != cfg_type:
            failures.append(f"type mismatch after save rec_id={rec_id}")
        if str(row.get("value_text") or "") != "edited":
            failures.append(f"edit not persisted rec_id={rec_id}")
        if str(row.get("scope_type") or "") != "global":
            failures.append(f"scope_type mismatch rec_id={rec_id}")

    if created_ids:
        details.append("create/edit/save ok")
        details.append(f"created={len(created_ids)}")

    _assert_menu_action_runtime(admin, failures, details)
    details.append(f"role_uid={role_uid}")
    details.append(f"role_login={config_admin_login}")

    if failures:
        raise SystemExit(
            "[native_business_admin_config_center_runtime_clickpath_verify] FAIL " + "; ".join(failures)
        )

    print("[native_business_admin_config_center_runtime_clickpath_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
