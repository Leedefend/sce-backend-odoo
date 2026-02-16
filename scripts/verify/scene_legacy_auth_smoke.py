#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from python_http_smoke_utils import get_base_url, http_get_json_with_headers
from scene_legacy_assertions import require_deprecation_headers


def main() -> None:
    base_url = get_base_url()
    scenes_url = f"{base_url}/api/scenes/my"

    status, payload, headers = http_get_json_with_headers(scenes_url, headers={})
    if status not in (401, 403):
        raise RuntimeError(f"scenes.my without auth should be 401/403, got {status}")
    if payload.get("ok") is not False:
        raise RuntimeError("scenes.my without auth should return error envelope")
    require_deprecation_headers(headers, label="scenes.my unauthenticated")
    error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    code = str(error.get("code") or "").strip().upper()
    if code not in {"AUTH_REQUIRED", "PERMISSION_DENIED"}:
        raise RuntimeError(f"scenes.my without auth unexpected error code: {code}")

    print("[scene_legacy_auth_smoke] PASS")


if __name__ == "__main__":
    main()
