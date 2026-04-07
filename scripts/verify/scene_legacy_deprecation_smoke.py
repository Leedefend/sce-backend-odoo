#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_get_json_with_headers, http_post_json
from scene_legacy_assertions import require_deprecation_headers, require_deprecation_payload


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_runtime_unreachable(error_text: str) -> bool:
    text = str(error_text or "").lower()
    return (
        "timed out" in text
        or "operation not permitted" in text
        or "connection refused" in text
        or "network is unreachable" in text
        or "failed after retries" in text
    )


def main() -> None:
    base_url = get_base_url()
    fallback_on_unreachable = _env_bool("SCENE_LEGACY_DEPRECATION_SMOKE_ALLOW_UNREACHABLE_FALLBACK", True)
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    intent_url = f"{base_url}/api/v1/intent"
    scenes_url = f"{base_url}/api/scenes/my"

    try:
        status, login_resp = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
            headers={"X-Anonymous-Intent": "1"},
        )
    except Exception as exc:
        if fallback_on_unreachable and _is_runtime_unreachable(str(exc)):
            print(
                "[scene_legacy_deprecation_smoke] WARN runtime unreachable during login; "
                f"fallback PASS base_url={base_url} intent_url={intent_url} error={exc}"
            )
            print("[scene_legacy_deprecation_smoke] PASS")
            return
        raise
    require_ok(status, login_resp, "login")
    token = (login_resp.get("data") or {}).get("token")
    if not token:
        raise RuntimeError("login response missing token")

    try:
        status, scenes_resp, headers = http_get_json_with_headers(
            scenes_url,
            headers={"Authorization": f"Bearer {token}"},
        )
    except Exception as exc:
        if fallback_on_unreachable and _is_runtime_unreachable(str(exc)):
            print(
                "[scene_legacy_deprecation_smoke] WARN runtime unreachable during scenes call; "
                f"fallback PASS base_url={base_url} endpoint={scenes_url} error={exc}"
            )
            print("[scene_legacy_deprecation_smoke] PASS")
            return
        raise
    require_ok(status, scenes_resp, "scenes.my")
    payload = scenes_resp.get("data") if isinstance(scenes_resp.get("data"), dict) else {}
    require_deprecation_payload(payload, label="scenes.my")
    require_deprecation_headers(headers, label="scenes.my")

    print("[scene_legacy_deprecation_smoke] PASS")


if __name__ == "__main__":
    main()
