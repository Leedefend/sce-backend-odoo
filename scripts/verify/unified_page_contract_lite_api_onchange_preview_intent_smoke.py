#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke api.onchange Lite preview through /api/v1/intent."""

from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


def _artifact_dir() -> Path:
    root = Path(os.getenv("ARTIFACTS_DIR") or "artifacts")
    path = root / "backend"
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return path
    except Exception:
        fallback = Path("/tmp/unified_page_contract_lite")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def _token_from_login(login_resp: dict) -> str:
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = session.get("token") or data.get("token")
    if not token:
        raise RuntimeError("login response missing token")
    return str(token)


def _post_intent(intent_url: str, intent: str, params: dict, *, token: str | None = None, anonymous: bool = False):
    headers = {}
    if token:
        headers["Authorization"] = "Bearer %s" % token
        headers["X-Odoo-DB"] = os.getenv("DB_NAME") or "sc_demo"
    if anonymous:
        headers["X-Anonymous-Intent"] = "1"
    return http_post_json(intent_url, {"intent": intent, "params": params}, headers=headers)


def _base_params() -> dict:
    return {
        "model": "project.project",
        "values": {"name": "Lite Intent Smoke"},
        "changed_fields": [],
        "context": {"lang": "zh_CN"},
    }


def _valid_opt_in() -> dict:
    params = _base_params()
    params.update(
        {
            "contractMode": "lite_preview",
            "contractVersion": "2.0.0",
            "entryPoint": "api_onchange",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
            "traceId": "lite-intent-smoke-001",
        }
    )
    return params


def _incomplete_opt_in() -> dict:
    params = _base_params()
    params.update(
        {
            "contractMode": "lite_preview",
            "entryPoint": "api_onchange",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
        }
    )
    return params


def _assert(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "123456"
    intent_url = "%s/api/v1/intent" % base_url
    errors: list[str] = []

    status, login_resp = _post_intent(
        intent_url,
        "login",
        {"db": db_name, "login": login, "password": password},
        anonymous=True,
    )
    require_ok(status, login_resp, "login")
    token = _token_from_login(login_resp)

    default_status, default_response = _post_intent(intent_url, "api.onchange", _base_params(), token=token)
    incomplete_status, incomplete_response = _post_intent(intent_url, "api.onchange", _incomplete_opt_in(), token=token)
    valid_status, valid_response = _post_intent(intent_url, "api.onchange", _valid_opt_in(), token=token)

    _assert(default_status == 200 and default_response.get("ok") is True, errors, "default api.onchange must be ok")
    _assert("lite_preview" not in default_response, errors, "default api.onchange must not include lite_preview")
    _assert(
        incomplete_status == 200 and incomplete_response.get("ok") is True,
        errors,
        "incomplete opt-in api.onchange must be ok",
    )
    _assert("lite_preview" not in incomplete_response, errors, "incomplete opt-in must not include lite_preview")
    _assert(valid_status == 200 and valid_response.get("ok") is True, errors, "valid opt-in api.onchange must be ok")
    _assert(
        valid_response.get("data") == default_response.get("data"),
        errors,
        "valid opt-in must keep legacy data unchanged",
    )

    preview = valid_response.get("lite_preview") if isinstance(valid_response, dict) else None
    _assert(isinstance(preview, dict), errors, "valid opt-in must include lite_preview")
    if isinstance(preview, dict):
        _assert(preview.get("contractMode") == "lite_preview", errors, "preview contractMode mismatch")
        _assert(preview.get("contractVersion") == "2.0.0", errors, "preview contractVersion mismatch")
        _assert(preview.get("entryPoint") == "api_onchange", errors, "preview entryPoint mismatch")
        _assert(preview.get("payloadType") == "lite_patch", errors, "preview payloadType mismatch")
        _assert(preview.get("fallbackMode") == "legacy_default", errors, "preview fallbackMode mismatch")
        meta = preview.get("meta") if isinstance(preview.get("meta"), dict) else {}
        _assert(meta.get("previewOnly") is True, errors, "preview meta.previewOnly must be true")
        _assert(meta.get("defaultUnchanged") is True, errors, "preview meta.defaultUnchanged must be true")
        _assert(meta.get("traceId") == "lite-intent-smoke-001", errors, "preview traceId must be preserved")
        payload = preview.get("payload") if isinstance(preview.get("payload"), dict) else {}
        _assert(payload.get("updateType") == "partial", errors, "preview payload must be partial")
        for key in ("statusPatch", "dataPatch", "layoutPatch"):
            _assert(isinstance(payload.get(key), dict), errors, "preview payload missing %s" % key)

    report = {
        "ok": not errors,
        "base_url": base_url,
        "db": db_name,
        "login": login,
        "default_status": default_status,
        "default_has_lite_preview": "lite_preview" in default_response,
        "incomplete_status": incomplete_status,
        "incomplete_has_lite_preview": "lite_preview" in incomplete_response,
        "valid_status": valid_status,
        "valid_has_lite_preview": isinstance(preview, dict),
        "valid_legacy_data_unchanged": valid_response.get("data") == default_response.get("data"),
        "preview_payload_type": preview.get("payloadType") if isinstance(preview, dict) else None,
        "errors": errors,
    }
    out = _artifact_dir() / "unified_page_contract_lite_api_onchange_preview_intent_smoke.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("[unified_page_contract_lite_api_onchange_preview_intent_smoke] FAIL")
        for error in errors:
            print("- %s" % error)
        print("report=%s" % out)
        raise SystemExit(1)

    print("[unified_page_contract_lite_api_onchange_preview_intent_smoke] PASS")
    print("report=%s" % out)


if __name__ == "__main__":
    main()
