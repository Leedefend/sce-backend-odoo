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


def _authenticate_with_fallback(
    base_url: str,
    db_name: str,
    logins: list[str],
    passwords: list[str],
) -> tuple[SessionClient | None, int, str, str]:
    for login in logins:
        normalized_login = str(login or "").strip()
        if not normalized_login:
            continue
        for password in passwords:
            normalized_password = str(password or "").strip()
            if not normalized_password:
                continue
            probe = SessionClient(base_url)
            uid = probe.authenticate(db_name, normalized_login, normalized_password)
            if uid > 0:
                return probe, uid, normalized_login, normalized_password
    return None, 0, "", ""


def _extract_home_blocks(body: dict) -> list[dict]:
    data = body.get("data") if isinstance(body, dict) else {}
    if not isinstance(data, dict):
        return []
    direct_rows = data.get("home_blocks")
    if isinstance(direct_rows, list):
        return direct_rows
    ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
    module_facts = ext_facts.get("smart_construction_core") if isinstance(ext_facts.get("smart_construction_core"), dict) else {}
    rows = module_facts.get("home_blocks")
    return rows if isinstance(rows, list) else []


def _validate_shape(role: str, rows: list[dict], failures: list[str], details: list[str]) -> None:
    for item in rows:
        if not isinstance(item, dict):
            failures.append(f"{role}: home-block group not dict")
            continue
        role_code = str(item.get("role_code") or "").strip()
        blocks = item.get("blocks")
        if not role_code:
            failures.append(f"{role}: empty role_code")
        if not isinstance(blocks, list):
            failures.append(f"{role}: blocks not list role_code={role_code}")
            continue
        for block in blocks:
            block_key = str(block or "").strip()
            if not block_key:
                failures.append(f"{role}: empty block key role_code={role_code}")
    details.append(f"{role}:groups={len(rows)}")


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    roles = [
        ("admin", ["admin"], ["admin"]),
        ("pm", ["sc_fx_pm", "demo_role_pm"], ["demo", "prod_like", "admin"]),
        ("finance", ["sc_fx_finance", "demo_role_finance"], ["demo", "prod_like", "admin"]),
        ("outsider", [outsider_login], ["demo", "prod_like", "admin"]),
    ]

    failures: list[str] = []
    details: list[str] = []

    for role, logins, passwords in roles:
        client, uid, used_login, _ = _authenticate_with_fallback(base_url, db_name, logins, passwords)
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

        rows = _extract_home_blocks(body)
        if role == "admin" and not rows:
            failures.append("admin: home_blocks missing")
            continue
        _validate_shape(role, rows, failures, details)
        details.append(f"{role}:uid={uid},login={used_login}")

    if failures:
        raise SystemExit("[native_business_admin_config_home_block_runtime_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_home_block_runtime_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
