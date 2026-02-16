#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json_with_headers, http_post_json
from scene_legacy_assertions import require_deprecation_headers, require_deprecation_payload


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"
    scenes_url = f"{base_url}/api/scenes/my"

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    status, scenes_resp, headers = http_get_json_with_headers(
        scenes_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, scenes_resp, "scenes.my")
    payload = scenes_resp.get("data") if isinstance(scenes_resp.get("data"), dict) else {}
    require_deprecation_payload(payload, label="scenes.my")
    require_deprecation_headers(headers, label="scenes.my")

    print("[scene_legacy_deprecation_smoke] PASS")


if __name__ == "__main__":
    main()
