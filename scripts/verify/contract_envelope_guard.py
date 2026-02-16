#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

REQUIRED_TOP_LEVEL_KEYS = ("ok", "data", "meta")


def _assert_envelope(payload: dict, *, label: str) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} payload must be object")
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in payload]
    if missing:
        raise RuntimeError(f"{label} missing envelope keys: {','.join(missing)}")
    if not isinstance(payload.get("meta"), dict):
        raise RuntimeError(f"{label} meta must be object")


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    _assert_envelope(login_resp, label="login")
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "user"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    _assert_envelope(init_resp, label="system.init")
    require_ok(status, init_resp, "system.init")

    status, contract_resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "tree", "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    _assert_envelope(contract_resp, label="ui.contract")
    require_ok(status, contract_resp, "ui.contract")

    print("[contract_envelope_guard] PASS")


if __name__ == "__main__":
    main()
