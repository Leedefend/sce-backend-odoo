#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify load_contract Lite preview across a small multi-model matrix."""

from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


DEFAULT_CASES = (
    ("project.project", "tree"),
    ("purchase.order", "tree"),
    ("payment.request", "tree"),
)


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


def _matrix_cases() -> list[tuple[str, str]]:
    raw = os.getenv("LITE_LOAD_CONTRACT_MATRIX") or ""
    if not raw.strip():
        return list(DEFAULT_CASES)
    cases: list[tuple[str, str]] = []
    for item in raw.split(","):
        part = item.strip()
        if not part:
            continue
        if ":" in part:
            model, view_type = part.split(":", 1)
        else:
            model, view_type = part, "tree"
        model = model.strip()
        view_type = view_type.strip() or "tree"
        if model:
            cases.append((model, view_type))
    return cases or list(DEFAULT_CASES)


def _load_contract(intent_url: str, headers: dict, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "load_contract", "params": params},
        headers=headers,
    )


def _base_params(model: str, view_type: str) -> dict:
    return {
        "model": model,
        "view_type": view_type,
        "include": "all",
    }


def _valid_params(model: str, view_type: str, trace_id: str) -> dict:
    return {
        **_base_params(model, view_type),
        "contractMode": "lite_preview",
        "contractVersion": "2.0.0",
        "entryPoint": "load_contract",
        "clientType": "web_pc",
        "fallbackMode": "legacy_default",
        "traceId": trace_id,
    }


def _assert(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
    login = os.getenv("E2E_LOGIN") or "cost1"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "123456"
    intent_url = "%s/api/v1/intent" % base_url
    errors: list[str] = []

    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    token = _token_from_login(login_resp)
    headers = {"Authorization": "Bearer %s" % token, "X-Odoo-DB": db_name}

    results = []
    for index, (model, view_type) in enumerate(_matrix_cases()):
        label = "%s:%s" % (model, view_type)
        default_status, default_response = _load_contract(intent_url, headers, _base_params(model, view_type))
        require_ok(default_status, default_response, "load_contract:%s:default" % label)
        _assert("lite_preview" not in default_response, errors, "%s default must not include lite_preview" % label)

        trace_id = "lite-load-contract-matrix-%02d" % index
        valid_status, valid_response = _load_contract(intent_url, headers, _valid_params(model, view_type, trace_id))
        require_ok(valid_status, valid_response, "load_contract:%s:valid_opt_in" % label)
        _assert(valid_response.get("data") == default_response.get("data"), errors, "%s valid opt-in must keep data unchanged" % label)

        preview = valid_response.get("lite_preview") if isinstance(valid_response, dict) else None
        _assert(isinstance(preview, dict), errors, "%s valid opt-in must include lite_preview" % label)
        payload = preview.get("payload") if isinstance(preview, dict) and isinstance(preview.get("payload"), dict) else {}
        if isinstance(preview, dict):
            _assert(preview.get("payloadType") == "lite_contract", errors, "%s preview payloadType mismatch" % label)
            _assert(preview.get("entryPoint") == "load_contract", errors, "%s preview entryPoint mismatch" % label)
            meta = preview.get("meta") if isinstance(preview.get("meta"), dict) else {}
            _assert(meta.get("traceId") == trace_id, errors, "%s preview traceId mismatch" % label)
            page_info = payload.get("pageInfo") if isinstance(payload.get("pageInfo"), dict) else {}
            _assert(page_info.get("model") == model, errors, "%s payload pageInfo.model mismatch" % label)
            _assert(page_info.get("viewType") == view_type, errors, "%s payload pageInfo.viewType mismatch" % label)
        for key in ("layoutContract", "statusContract", "actionContract", "dataContract"):
            _assert(isinstance(payload.get(key), dict), errors, "%s payload missing %s" % (label, key))

        results.append(
            {
                "model": model,
                "view_type": view_type,
                "default_has_lite_preview": "lite_preview" in default_response,
                "valid_has_lite_preview": isinstance(preview, dict),
                "valid_legacy_data_unchanged": valid_response.get("data") == default_response.get("data"),
                "payload_type": preview.get("payloadType") if isinstance(preview, dict) else None,
            }
        )

    report = {
        "ok": not errors,
        "base_url": base_url,
        "db": db_name,
        "login": login,
        "case_count": len(results),
        "results": results,
        "errors": errors,
    }
    out = _artifact_dir() / "unified_page_contract_lite_load_contract_preview_matrix_smoke.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("[unified_page_contract_lite_load_contract_preview_matrix_smoke] FAIL")
        for error in errors:
            print("- %s" % error)
        print("report=%s" % out)
        raise SystemExit(1)

    print("[unified_page_contract_lite_load_contract_preview_matrix_smoke] PASS")
    print("case_count=%s" % len(results))
    print("report=%s" % out)


if __name__ == "__main__":
    main()
