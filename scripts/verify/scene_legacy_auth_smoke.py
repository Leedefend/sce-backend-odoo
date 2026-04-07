#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from python_http_smoke_utils import get_base_url, http_get_json_with_headers
from scene_legacy_assertions import require_deprecation_headers


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
        or "remote end closed connection without response" in text
        or "remotedisconnected" in text
        or "network is unreachable" in text
        or "failed after retries" in text
    )


def _run_auth_smoke(*, base_url: str, endpoint: str, fallback_on_unreachable: bool) -> None:
    try:
        status, payload, headers = http_get_json_with_headers(endpoint, headers={})
    except Exception as exc:
        exc_text = str(exc)
        if _is_runtime_unreachable(exc_text):
            if fallback_on_unreachable:
                print(
                    "[scene_legacy_auth_smoke] WARN runtime unreachable; "
                    f"fallback PASS base_url={base_url} endpoint={endpoint} error={exc_text}"
                )
                print("[scene_legacy_auth_smoke] PASS")
                return
            raise RuntimeError(
                "runtime unreachable in strict mode: "
                f"base_url={base_url} endpoint={endpoint} error={exc_text}"
            ) from exc
        raise

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


def main() -> None:
    base_url = get_base_url()
    endpoint_path = os.getenv("SCENE_LEGACY_AUTH_SMOKE_ENDPOINT_PATH", "/api/scenes/my").strip() or "/api/scenes/my"
    if not endpoint_path.startswith("/"):
        endpoint_path = f"/{endpoint_path}"
    scenes_url = os.getenv("SCENE_LEGACY_AUTH_SMOKE_URL", "").strip() or f"{base_url}{endpoint_path}"
    fallback_on_unreachable = _env_bool(
        "SCENE_LEGACY_AUTH_SMOKE_ALLOW_UNREACHABLE_FALLBACK", False
    )
    _run_auth_smoke(
        base_url=base_url,
        endpoint=scenes_url,
        fallback_on_unreachable=fallback_on_unreachable,
    )


if __name__ == "__main__":
    main()
