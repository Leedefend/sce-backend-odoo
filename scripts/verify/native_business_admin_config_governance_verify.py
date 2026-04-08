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
        return int((result or {}).get("uid") or 0)

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


def _login_with_fallback(base_url: str, db_name: str, login: str, passwords: list[str]) -> tuple[OdooSession | None, str]:
    for password in passwords:
        session = OdooSession(base_url)
        try:
            if session.authenticate(db_name, login, password) > 0:
                return session, password
        except Exception:
            continue
    return None, ""


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    failures: list[str] = []
    details: list[str] = []

    admin, admin_pwd = _login_with_fallback(base_url, db_name, "admin", ["admin"])
    if not admin:
        raise SystemExit("[native_business_admin_config_governance_verify] FAIL admin auth failed")
    details.append(f"admin_auth={admin_pwd}")

    # ensure outsider exists with minimal group
    base_group_ref = admin.call_kw(
        "ir.model.data",
        "search_read",
        [[("module", "=", "base"), ("name", "=", "group_user")]],
        {"fields": ["res_id"], "limit": 1},
    )
    base_group_id = int(base_group_ref[0]["res_id"]) if base_group_ref else 0
    outsider_rows = admin.call_kw(
        "res.users",
        "search_read",
        [[("login", "=", outsider_login)]],
        {"fields": ["id"], "limit": 1},
    )
    outsider_vals = {"name": "Fixture Outsider", "login": outsider_login, "password": "demo"}
    if base_group_id > 0:
        outsider_vals["groups_id"] = [(6, 0, [base_group_id])]
    if outsider_rows:
        admin.call_kw("res.users", "write", [[int(outsider_rows[0]["id"])], outsider_vals], {})
    else:
        admin.call_kw("res.users", "create", [outsider_vals], {})

    # admin governance checks
    required_types = ["system_param", "role_entry", "home_block"]
    for config_type in required_types:
        count = int(
            admin.call_kw("sc.dictionary", "search_count", [[("type", "=", config_type)]], {}) or 0
        )
        if count <= 0:
            failures.append(f"missing config type records: {config_type}")
        else:
            details.append(f"{config_type}_count={count}")

    # admin write roundtrip
    rows = admin.call_kw(
        "sc.dictionary",
        "search_read",
        [[("type", "=", "system_param")]],
        {"fields": ["id", "note"], "limit": 1},
    )
    if not rows:
        failures.append("system_param sample missing for write roundtrip")
    else:
        rec_id = int(rows[0]["id"])
        mark = f"governance-verify-{int(time.time())}"
        admin.call_kw("sc.dictionary", "write", [[rec_id], {"note": mark}], {})
        after = admin.call_kw("sc.dictionary", "read", [[rec_id], ["note"]], {})
        got = str((after[0] if after else {}).get("note") or "")
        if mark not in got:
            failures.append("admin write roundtrip failed")
        else:
            details.append("admin_write_roundtrip=ok")

    # outsider deny checks
    outsider, outsider_pwd = _login_with_fallback(base_url, db_name, outsider_login, ["demo", "prod_like", "admin"])
    if not outsider:
        failures.append("outsider auth failed")
    else:
        details.append(f"outsider_auth={outsider_pwd}")
        rights = {}
        for op in ("read", "write", "create", "unlink"):
            rights[op] = bool(
                outsider.call_kw("sc.dictionary", "check_access_rights", [op], {"raise_exception": False})
            )
        if any(rights.values()):
            failures.append(f"outsider rights leaked: {rights}")
        else:
            details.append("outsider_rights=deny_all")

    if failures:
        raise SystemExit("[native_business_admin_config_governance_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_governance_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
