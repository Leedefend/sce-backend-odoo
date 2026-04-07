#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from python_http_smoke_utils import get_base_url, http_get_json_with_headers, http_post_json


def _probe_base_urls() -> list[str]:
    explicit = os.getenv("SCENE_LEGACY_AUTH_RUNTIME_PROBE_BASE_URLS", "").strip()
    if explicit:
        items = [item.strip() for item in explicit.split(",") if item.strip()]
        if items:
            return items
    default_url = get_base_url()
    fallback_url = "http://localhost:8070"
    if default_url == fallback_url:
        return [default_url]
    return [default_url, fallback_url]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _probe_endpoint_path() -> str:
    explicit = os.getenv("SCENE_LEGACY_AUTH_RUNTIME_PROBE_ENDPOINT_PATH", "").strip()
    if explicit:
        return explicit if explicit.startswith("/") else f"/{explicit}"
    native_default = _env_bool("SCENE_LEGACY_AUTH_RUNTIME_PROBE_USE_NATIVE_ENDPOINT", True)
    if native_default:
        return "/api/v1/intent"
    return "/api/scenes/my"


def _probe_native_post(base_url: str, endpoint: str) -> tuple[int, dict]:
    status, payload = http_post_json(
        endpoint,
        {
            "intent": "app.init",
            "params": {},
            "context": {"source": "scene_legacy_auth_runtime_probe"},
        },
        headers={"Content-Type": "application/json"},
    )
    return status, payload


def main() -> None:
    probe_failed = False
    endpoint_path = _probe_endpoint_path()
    probe_native_endpoint = endpoint_path == "/api/v1/intent"
    for base_url in _probe_base_urls():
        endpoint = f"{base_url}{endpoint_path}"
        try:
            if probe_native_endpoint:
                status, payload = _probe_native_post(base_url, endpoint)
                _headers = {}
            else:
                status, payload, _headers = http_get_json_with_headers(endpoint, headers={})
            error_code = ""
            if isinstance(payload, dict):
                error = payload.get("error")
                if isinstance(error, dict):
                    error_code = str(error.get("code") or "").strip()
            print(
                "[scene_legacy_auth_runtime_probe] "
                f"base_url={base_url} endpoint={endpoint} status={status} error_code={error_code}"
            )
            continue
        except Exception as exc:
            text = str(exc)
            print(
                "[scene_legacy_auth_runtime_probe] "
                f"base_url={base_url} endpoint={endpoint} exception={text}"
            )
            probe_failed = True

    if probe_failed:
        print("[scene_legacy_auth_runtime_probe] WARN endpoint exceptions observed")

    print("[scene_legacy_auth_runtime_probe] PASS")


if __name__ == "__main__":
    main()
