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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_cost_tracking_block_contract_guard.json"

RESPONSE_KEYS = {"project_id", "block_key", "block", "degraded"}
SUPPORTED = {
    "summary": "fact_summary",
    "recent_moves": "record_list",
    "next_actions": "action_list",
}
BLOCK_KEYS = {"block_key", "block_type", "title", "state", "visibility", "data", "error"}


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
        token = str(((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token") or "")).strip()
        if not token:
            raise RuntimeError("login token missing")

        status, create_resp = _post(intent_url, token, "project.initiation.enter", {
            "name": f"P17A-COST-BLOCK-{uuid4().hex[:8]}",
            "description": "cost tracking block contract guard",
            "date_start": str(os.getenv("P17A_DATE_START") or "2026-03-23"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        for block_key, expected_type in SUPPORTED.items():
            status, block_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": block_key}, db_name=db_name)
            _assert_ok(status, block_resp, f"cost.tracking.block.fetch({block_key})")
            data = block_resp.get("data") if isinstance(block_resp.get("data"), dict) else {}
            if set(data.keys()) != RESPONSE_KEYS:
                raise RuntimeError(f"block response keys drift for {block_key}: {sorted(data.keys())}")
            if int(data.get("project_id") or 0) != project_id:
                raise RuntimeError(f"block project_id mismatch for {block_key}")
            if str(data.get("block_key") or "").strip() != block_key:
                raise RuntimeError(f"block key mismatch for {block_key}")
            block = data.get("block") if isinstance(data.get("block"), dict) else {}
            if set(block.keys()) != BLOCK_KEYS:
                raise RuntimeError(f"block envelope keys drift for {block_key}: {sorted(block.keys())}")
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
        print("[product_cost_tracking_block_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_cost_tracking_block_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
