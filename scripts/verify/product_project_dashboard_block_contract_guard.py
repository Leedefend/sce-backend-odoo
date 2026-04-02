#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

from python_http_smoke_utils import get_base_url, http_post_json

ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_dashboard_block_contract_guard.json"

REQUIRED_RESPONSE_KEYS = {"project_id", "block_key", "block"}
OPTIONAL_RESPONSE_KEYS = {"degraded", "project_context"}
SUPPORTED = {
    "progress": "progress_summary",
    "risks": "alert_panel",
    "next_actions": "action_list",
}
REQUIRED_BLOCK_KEYS = {"block_key", "block_type", "title", "state", "visibility", "data"}
OPTIONAL_BLOCK_KEYS = {"error"}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _extract_login_token(login_resp: dict) -> str:
    data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "blocks": {}}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = _extract_login_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, create_resp = _post(intent_url, token, "project.initiation.enter", {
            "name": f"P12E-E5-BLOCK-{uuid4().hex[:8]}",
            "description": "dashboard block contract guard",
            "date_start": str(os.getenv("P12E_DATE_START") or "2026-03-22"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        for block_key, expected_type in SUPPORTED.items():
            status, block_resp = _post(intent_url, token, "project.dashboard.block.fetch", {"project_id": project_id, "block_key": block_key}, db_name=db_name)
            _assert_ok(status, block_resp, f"project.dashboard.block.fetch({block_key})")
            data = block_resp.get("data") if isinstance(block_resp.get("data"), dict) else {}
            data_keys = set(data.keys())
            missing_response_keys = sorted(REQUIRED_RESPONSE_KEYS - data_keys)
            if missing_response_keys:
                raise RuntimeError(f"block response missing required keys for {block_key}: {missing_response_keys}")
            unknown_response_keys = sorted(data_keys - REQUIRED_RESPONSE_KEYS - OPTIONAL_RESPONSE_KEYS)
            if unknown_response_keys:
                raise RuntimeError(f"block response keys drift for {block_key}: {unknown_response_keys}")
            if int(data.get("project_id") or 0) != project_id:
                raise RuntimeError(f"block project_id mismatch for {block_key}")
            if str(data.get("block_key") or "").strip() != block_key:
                raise RuntimeError(f"block key mismatch for {block_key}")
            block = data.get("block") if isinstance(data.get("block"), dict) else {}
            block_keys = set(block.keys())
            missing_block_keys = sorted(REQUIRED_BLOCK_KEYS - block_keys)
            if missing_block_keys:
                raise RuntimeError(f"block envelope missing required keys for {block_key}: {missing_block_keys}")
            unknown_block_keys = sorted(block_keys - REQUIRED_BLOCK_KEYS - OPTIONAL_BLOCK_KEYS)
            if unknown_block_keys:
                raise RuntimeError(f"block envelope keys drift for {block_key}: {unknown_block_keys}")
            if str(block.get("block_type") or "").strip() != expected_type:
                raise RuntimeError(f"block type drift for {block_key}: {block.get('block_type')!r}")
            report["blocks"][block_key] = {
                "state": str(block.get("state") or ""),
                "block_type": str(block.get("block_type") or ""),
                "degraded": bool(data.get("degraded")),
            }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_dashboard_block_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_dashboard_block_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
