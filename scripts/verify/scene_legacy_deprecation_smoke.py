#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json_with_headers, http_post_json


def _require_deprecation_payload(payload: dict, *, label: str) -> None:
    dep = payload.get("deprecation") if isinstance(payload.get("deprecation"), dict) else {}
    if (dep.get("status") or "").strip().lower() != "deprecated":
        raise RuntimeError(f"{label} missing deprecation.status=deprecated")
    if not str(dep.get("replacement") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.replacement")
    if not str(dep.get("sunset_date") or "").strip():
        raise RuntimeError(f"{label} missing deprecation.sunset_date")


def _require_deprecation_headers(headers: dict, *, label: str) -> None:
    dep_header = str(headers.get("Deprecation") or headers.get("deprecation") or "").strip().lower()
    if dep_header != "true":
        raise RuntimeError(f"{label} missing Deprecation header=true")
    sunset_header = str(headers.get("Sunset") or headers.get("sunset") or "").strip()
    if not sunset_header:
        raise RuntimeError(f"{label} missing Sunset header")
    link_header = str(headers.get("Link") or headers.get("link") or "").strip()
    if "successor-version" not in link_header or "/api/v1/intent" not in link_header:
        raise RuntimeError(f"{label} missing Link successor-version header")


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
    _require_deprecation_payload(payload, label="scenes.my")
    _require_deprecation_headers(headers, label="scenes.my")

    print("[scene_legacy_deprecation_smoke] PASS")


if __name__ == "__main__":
    main()
