#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

from python_http_smoke_utils import get_base_url, http_post_json


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None) -> tuple[int, dict]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    if not isinstance(payload, dict):
        payload = {}
    return status, payload


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"

    status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password})
    _assert_ok(status, login_resp, "login")
    token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
    if not str(token or "").strip():
        raise RuntimeError("login response missing data.session.token")

    status, init_resp = _post(intent_url, token, "system.init", {"contract_mode": "user"})
    _assert_ok(status, init_resp, "system.init")

    status, catalog_resp = _post(intent_url, token, "app.catalog", {})
    _assert_ok(status, catalog_resp, "app.catalog")
    catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
    apps = catalog_data.get("apps") if isinstance(catalog_data.get("apps"), list) else []
    if not apps:
        raise RuntimeError("app.catalog returned empty apps")
    first_app = apps[0] if isinstance(apps[0], dict) else {}
    app_id = str((first_app.get("meta") or {}).get("app_id") or "").strip() or str(first_app.get("key") or "app:workspace").replace("app:", "", 1)

    status, nav_resp = _post(intent_url, token, "app.nav", {"app": app_id})
    _assert_ok(status, nav_resp, "app.nav")

    status, open_resp = _post(intent_url, token, "app.open", {"app": app_id})
    _assert_ok(status, open_resp, "app.open")
    open_data = open_resp.get("data") if isinstance(open_resp.get("data"), dict) else {}
    if str(open_data.get("subject") or "") != "ui.contract":
        raise RuntimeError("app.open did not return ui.contract subject")

    print("[smart_core_owner_startup_smoke] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("[smart_core_owner_startup_smoke] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
