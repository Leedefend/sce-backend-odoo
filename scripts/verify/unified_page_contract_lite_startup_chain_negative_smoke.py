#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Lite preview opt-in does not affect startup-chain intents."""

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


def _lite_noise(entry_point: str) -> dict:
    return {
        "contractMode": "lite_preview",
        "contractVersion": "2.0.0",
        "entryPoint": entry_point,
        "clientType": "web_pc",
        "fallbackMode": "legacy_default",
        "traceId": "lite-startup-negative-001",
    }


def _assert_no_lite(payload: dict, errors: list[str], label: str) -> None:
    if "lite_preview" in payload:
        errors.append("%s must not include top-level lite_preview" % label)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    if "lite_preview" in data:
        errors.append("%s data must not include lite_preview" % label)


def main() -> None:
    base_url = get_base_url()
    db_name = os.getenv("DB_NAME") or os.getenv("E2E_DB") or "sc_demo"
    login = os.getenv("E2E_LOGIN") or "cost1"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "123456"
    intent_url = "%s/api/v1/intent" % base_url
    errors: list[str] = []

    login_params = {"db": db_name, "login": login, "password": password}
    login_params.update(_lite_noise("login"))
    status, login_resp = http_post_json(
        intent_url,
        {"intent": "login", "params": login_params},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, login_resp, "login")
    _assert_no_lite(login_resp, errors, "login")
    token = _token_from_login(login_resp)

    headers = {"Authorization": "Bearer %s" % token, "X-Odoo-DB": db_name}
    init_params = {"contract_mode": "user"}
    init_params.update(_lite_noise("system_init"))
    init_status, init_resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": init_params},
        headers=headers,
    )
    require_ok(init_status, init_resp, "system.init")
    _assert_no_lite(init_resp, errors, "system.init")

    contract_params = {
        "op": "model",
        "model": "project.project",
        "view_type": "tree",
        "contract_mode": "user",
    }
    contract_params.update(_lite_noise("ui_contract"))
    contract_status, contract_resp = http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": contract_params},
        headers=headers,
    )
    require_ok(contract_status, contract_resp, "ui.contract")
    _assert_no_lite(contract_resp, errors, "ui.contract")

    report = {
        "ok": not errors,
        "base_url": base_url,
        "db": db_name,
        "login": login,
        "login_status": status,
        "system_init_status": init_status,
        "ui_contract_status": contract_status,
        "login_has_lite_preview": "lite_preview" in login_resp,
        "system_init_has_lite_preview": "lite_preview" in init_resp,
        "ui_contract_has_lite_preview": "lite_preview" in contract_resp,
        "errors": errors,
    }
    out = _artifact_dir() / "unified_page_contract_lite_startup_chain_negative_smoke.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if errors:
        print("[unified_page_contract_lite_startup_chain_negative_smoke] FAIL")
        for error in errors:
            print("- %s" % error)
        print("report=%s" % out)
        raise SystemExit(1)

    print("[unified_page_contract_lite_startup_chain_negative_smoke] PASS")
    print("report=%s" % out)


if __name__ == "__main__":
    main()
