#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

from python_http_smoke_utils import get_base_url, http_post_json


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None) -> tuple[int, dict]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, payload = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password})
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"login failed: status={status}")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = ((data.get("session") or {}).get("token") if isinstance(data.get("session"), dict) else None) or data.get("token")
    token = str(token or "").strip()
    if not token:
        raise RuntimeError("login token missing")
    return token


def _app_id(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
    text = str(meta.get("app_id") or "").strip()
    if text:
        return text
    return str(item.get("key") or "").replace("app:", "", 1).strip()


def _assert_open_ok(intent_url: str, token: str, app_id: str, label: str) -> None:
    status, payload = _post(intent_url, token, "app.open", {"app": app_id})
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label}: app.open failed for app={app_id}, status={status}, payload={payload}")
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    subject = str(data.get("subject") or "").strip()
    if not subject:
        raise RuntimeError(f"{label}: app.open returned empty subject for app={app_id}")


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    intent_url = f"{base_url}/api/v1/intent"

    owner_login = str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip()
    owner_password = str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip()
    admin_login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    admin_password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    owner_token = _login(intent_url, db_name, owner_login, owner_password)
    admin_token = _login(intent_url, db_name, admin_login, admin_password)

    for label, token in (("owner", owner_token), ("admin", admin_token)):
        status, catalog_resp = _post(intent_url, token, "app.catalog", {})
        if status >= 400 or catalog_resp.get("ok") is not True:
            raise RuntimeError(f"{label}: app.catalog failed status={status}")
        catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
        apps = catalog_data.get("apps") if isinstance(catalog_data.get("apps"), list) else []
        if not apps:
            raise RuntimeError(f"{label}: app.catalog empty")
        for app in apps:
            app_id = _app_id(app)
            if not app_id:
                continue
            _assert_open_ok(intent_url, token, app_id, label)

    print("[smart_core_app_open_fallback_regression_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("[smart_core_app_open_fallback_regression_guard] FAIL")
        print(f" - {exc}")
        sys.exit(1)

