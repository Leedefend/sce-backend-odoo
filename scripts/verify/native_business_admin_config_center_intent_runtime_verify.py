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


def _try_auth(base_url: str, db_name: str, login: str, passwords: list[str]) -> tuple[SessionClient | None, str]:
    for password in passwords:
        client = SessionClient(base_url)
        uid = client.authenticate(db_name, login, password)
        if uid > 0:
            return client, password
    return None, ""


def _intent_call(client: SessionClient, intent: str, params: dict) -> tuple[int, dict]:
    return client.post(
        "/api/v1/intent",
        {"intent": intent, "params": params},
        headers={"X-Anonymous-Intent": "1"},
    )


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

    for role, login, passwords in roles:
        client, used_password = _try_auth(base_url, db_name, login, passwords)
        if not client:
            failures.append(f"{role}: auth failed")
            continue

        details.append(f"{role}:session-ok({used_password})")

        status_init, body_init = _intent_call(client, "system.init", {"contract_mode": "user"})
        if status_init != 200 or not isinstance(body_init, dict) or body_init.get("ok") is not True:
            failures.append(f"{role}: system.init not ok status={status_init}")
            continue

        status_contract, body_contract = _intent_call(
            client,
            "ui.contract",
            {"op": "model", "model": "sc.dictionary", "view_type": "form", "contract_mode": "user"},
        )

        if status_contract != 200 or not isinstance(body_contract, dict) or body_contract.get("ok") is not True:
            failures.append(f"{role}: ui.contract not ok status={status_contract}")
        else:
            details.append(f"{role}:contract-ok")

    if failures:
        raise SystemExit("[native_business_admin_config_center_intent_runtime_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_center_intent_runtime_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
