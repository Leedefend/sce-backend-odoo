#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import sys

from python_http_smoke_utils import get_base_url, http_post_json


def _post(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict | None = None,
    *,
    db_name: str = "",
) -> tuple[int, dict]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
    _assert_ok(status, login_resp, "login")
    token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
    if not str(token or "").strip():
        raise RuntimeError("login response missing data.session.token")

    status, catalog_resp = _post(intent_url, token, "app.catalog", {}, db_name=db_name)
    _assert_ok(status, catalog_resp, "app.catalog")
    catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
    apps = catalog_data.get("apps") if isinstance(catalog_data.get("apps"), list) else []
    if not apps:
        raise RuntimeError("app.catalog returned empty apps")

    has_workspace = False
    for item in apps:
        if not isinstance(item, dict):
            continue
        app_id = str((item.get("meta") or {}).get("app_id") or "").strip() or str(item.get("key") or "").replace("app:", "", 1)
        if app_id == "workspace":
            has_workspace = True
            break
    if not has_workspace:
        raise RuntimeError("minimum surface baseline broken: workspace app missing in app.catalog")

    status, nav_resp = _post(intent_url, token, "app.nav", {"app": "workspace"}, db_name=db_name)
    _assert_ok(status, nav_resp, "app.nav(workspace)")

    status, open_resp = _post(intent_url, token, "app.open", {"app": "workspace"}, db_name=db_name)
    _assert_ok(status, open_resp, "app.open(workspace)")

    print("[smart_core_minimum_surface_order_regression_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("[smart_core_minimum_surface_order_regression_guard] FAIL")
        print(f" - {exc}")
        sys.exit(1)
