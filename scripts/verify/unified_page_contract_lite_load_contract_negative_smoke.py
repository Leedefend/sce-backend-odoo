#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Lite preview opt-in does not affect load_contract."""

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


def _assert_no_lite(payload: dict, errors: list[str], label: str) -> None:
    if "lite_preview" in payload:
        errors.append("%s must not include top-level lite_preview" % label)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if "lite_preview" in data:
        errors.append("%s data must not include lite_preview" % label)


def _load_contract(intent_url: str, headers: dict, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "load_contract", "params": params},
        headers=headers,
    )


def _base_params() -> dict:
    return {
        "model": "project.project",
        "view_type": "tree",
        "include": "all",
    }


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
    cases = {
        "default": _base_params(),
        "incomplete_opt_in": {
            **_base_params(),
            "contractMode": "lite_preview",
            "entryPoint": "load_contract",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
        },
        "wrong_entry_point": {
            **_base_params(),
            "contractMode": "lite_preview",
            "contractVersion": "2.0.0",
            "entryPoint": "api_onchange",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
        },
        "wrong_version": {
            **_base_params(),
            "contractMode": "lite_preview",
            "contractVersion": "1.0.0",
            "entryPoint": "load_contract",
            "clientType": "web_pc",
            "fallbackMode": "legacy_default",
        },
    }
    case_reports = {}
    for label, params in cases.items():
        contract_status, contract_resp = _load_contract(intent_url, headers, params)
        require_ok(contract_status, contract_resp, "load_contract:%s" % label)
        _assert_no_lite(contract_resp, errors, "load_contract:%s" % label)
        data = contract_resp.get("data") if isinstance(contract_resp.get("data"), dict) else {}
        case_reports[label] = {
            "status": contract_status,
            "has_lite_preview": "lite_preview" in contract_resp,
            "data_has_lite_preview": "lite_preview" in data,
        }

    report = {
        "ok": not errors,
        "base_url": base_url,
        "db": db_name,
        "login": login,
        "cases": case_reports,
        "errors": errors,
    }
    out = _artifact_dir() / "unified_page_contract_lite_load_contract_negative_smoke.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("[unified_page_contract_lite_load_contract_negative_smoke] FAIL")
        for error in errors:
            print("- %s" % error)
        print("report=%s" % out)
        raise SystemExit(1)

    print("[unified_page_contract_lite_load_contract_negative_smoke] PASS")
    print("report=%s" % out)


if __name__ == "__main__":
    main()
