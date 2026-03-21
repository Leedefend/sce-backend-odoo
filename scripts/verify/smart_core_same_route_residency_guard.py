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

    status, first_open = _post(intent_url, token, "app.open", {"app": "workspace"})
    _assert_ok(status, first_open, "app.open first")
    first_data = first_open.get("data") if isinstance(first_open.get("data"), dict) else {}
    scene_key = str(first_data.get("scene_key") or "").strip()
    route = str(first_data.get("route") or "").strip()
    if not scene_key or not route:
        raise RuntimeError("app.open first response missing scene_key/route")

    status, second_open = _post(intent_url, token, "app.open", {"scene_key": scene_key})
    _assert_ok(status, second_open, "app.open second")
    second_data = second_open.get("data") if isinstance(second_open.get("data"), dict) else {}
    if str(second_data.get("scene_key") or "").strip() != scene_key:
        raise RuntimeError("same-route guard: scene_key is not stable across repeated app.open")
    if str(second_data.get("route") or "").strip() != route:
        raise RuntimeError("same-route guard: route is not stable across repeated app.open")

    print("[smart_core_same_route_residency_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("[smart_core_same_route_residency_guard] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
