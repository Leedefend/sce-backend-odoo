#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json, http_post_json


def main():
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"

    intent_url = f"{base_url}/api/v1/intent"
    lint_url = f"{base_url}/api/capabilities/lint"
    ignore_keys = (os.getenv("CAPABILITY_LINT_IGNORE") or "").strip()
    if ignore_keys:
        lint_url = f"{lint_url}?ignore_keys={ignore_keys}"

    login_payload = {
        "intent": "login",
        "params": {"db": db_name, "login": login, "password": password},
    }
    status, login_resp = http_post_json(
        intent_url, login_payload, headers={"X-Anonymous-Intent": "1"}
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")
    auth_header = {"Authorization": f"Bearer {token}"}

    status, lint_resp = http_get_json(lint_url, headers=auth_header)
    require_ok(status, lint_resp, "capabilities.lint")
    data = lint_resp.get("data") or {}
    if data.get("status") != "pass":
        raise RuntimeError(f"capability lint failed: {data}")

    print("[capability_lint] PASS")


if __name__ == "__main__":
    main()
