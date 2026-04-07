#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import io
from contextlib import redirect_stdout


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    smoke = importlib.import_module("scene_legacy_auth_smoke")

    test_base_url = "http://localhost:8069"
    test_endpoint = f"{test_base_url}/api/scenes/my"
    test_headers = {
        "Deprecation": "true",
        "Sunset": "Thu, 30 Apr 2026 00:00:00 GMT",
        "Link": '<http://localhost:8069/api/v1/intent?intent=app.init>; rel="successor-version"',
        "X-Legacy-Endpoint": "scenes.my",
    }

    def unreachable_fetch(_url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
        raise RuntimeError(
            "HTTP request failed after retries: method=GET url=http://localhost:8069/api/scenes/my "
            "retries=3 timeout=30s last_error=URLError: <urlopen error [Errno 111] Connection refused>"
        )

    def auth_401_fetch(_url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
        return 401, {"ok": False, "error": {"code": "AUTH_REQUIRED"}}, test_headers

    def auth_403_fetch(_url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
        return 403, {"ok": False, "error": {"code": "PERMISSION_DENIED"}}, test_headers

    def remote_disconnected_fetch(_url: str, headers: dict | None = None) -> tuple[int, dict, dict]:
        raise RuntimeError(
            "HTTP request failed after retries: method=GET url=http://localhost:8069/api/scenes/my "
            "retries=3 timeout=30s last_error=RemoteDisconnected: Remote end closed connection without response"
        )

    original_fetch = smoke.http_get_json_with_headers
    try:
        smoke.http_get_json_with_headers = unreachable_fetch
        strict_failed = False
        try:
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=False,
            )
        except RuntimeError as exc:
            strict_failed = True
            text = str(exc)
            _assert("runtime unreachable in strict mode" in text, "strict mode error prefix missing")
            _assert(test_base_url in text, "strict mode error missing base_url")
            _assert(test_endpoint in text, "strict mode error missing endpoint")
            _assert("Connection refused" in text, "strict mode error missing original exception")
        _assert(strict_failed, "runtime unreachable should fail in strict mode")

        with redirect_stdout(io.StringIO()):
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=True,
            )

        smoke.http_get_json_with_headers = auth_401_fetch
        with redirect_stdout(io.StringIO()):
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=False,
            )

        smoke.http_get_json_with_headers = auth_403_fetch
        with redirect_stdout(io.StringIO()):
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=False,
            )

        smoke.http_get_json_with_headers = remote_disconnected_fetch
        remote_strict_failed = False
        try:
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=False,
            )
        except RuntimeError as exc:
            remote_strict_failed = True
            text = str(exc)
            _assert("runtime unreachable in strict mode" in text, "remote strict error prefix missing")
            _assert("RemoteDisconnected" in text, "remote strict error missing original exception")
        _assert(remote_strict_failed, "RemoteDisconnected should fail in strict mode")

        with redirect_stdout(io.StringIO()):
            smoke._run_auth_smoke(
                base_url=test_base_url,
                endpoint=test_endpoint,
                fallback_on_unreachable=True,
            )
    finally:
        smoke.http_get_json_with_headers = original_fetch

    print("[scene_legacy_auth_smoke_semantic_verify] PASS")


if __name__ == "__main__":
    main()
