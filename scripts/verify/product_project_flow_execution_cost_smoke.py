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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_execution_cost_smoke.json"


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

    report: dict = {"status": "PASS"}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = str(((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token") or "")).strip()
        if not token:
            raise RuntimeError("login token missing")

        status, initiation_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P17A-EXEC-COST-{uuid4().hex[:8]}",
                "description": "Phase 17-A execution to cost smoke",
                "date_start": str(os.getenv("P17A_DATE_START") or "2026-03-23"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        project_id = int((((initiation_data.get("record") or {}) if isinstance(initiation_data.get("record"), dict) else {}).get("id") or 0))
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        status, execution_resp = _post(intent_url, token, "project.execution.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, execution_resp, "project.execution.enter")
        execution_entry = execution_resp.get("data") if isinstance(execution_resp.get("data"), dict) else {}
        execution_hints = (((execution_entry.get("runtime_fetch_hints") or {}) if isinstance(execution_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        status, execution_next_resp = _post(intent_url, token, "project.execution.block.fetch", ((execution_hints.get("next_actions") or {}) if isinstance(execution_hints.get("next_actions"), dict) else {}).get("params") or {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, execution_next_resp, "project.execution.block.fetch(next_actions)")
        execution_next_block = (((execution_next_resp.get("data") or {}).get("block")) or {})
        next_actions = ((((execution_next_block.get("data") or {}) if isinstance(execution_next_block.get("data"), dict) else {}).get("actions")) or [])
        cost_action = next((row for row in next_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "cost.tracking.enter"), None)
        if not isinstance(cost_action, dict):
            raise RuntimeError("execution next_actions missing cost.tracking.enter")
        cost_params = cost_action.get("params") if isinstance(cost_action.get("params"), dict) else {}
        if int(cost_params.get("project_id") or 0) != project_id:
            raise RuntimeError("execution->cost project_id mismatch")

        status, cost_entry_resp = _post(intent_url, token, "cost.tracking.enter", cost_params, db_name=db_name)
        _assert_ok(status, cost_entry_resp, "cost.tracking.enter")
        cost_entry = cost_entry_resp.get("data") if isinstance(cost_entry_resp.get("data"), dict) else {}
        if int(cost_entry.get("project_id") or 0) != project_id:
            raise RuntimeError("cost entry project_id mismatch")
        if str(cost_entry.get("scene_key") or "").strip() != "cost.tracking":
            raise RuntimeError("cost scene_key mismatch")
        cost_hints = (((cost_entry.get("runtime_fetch_hints") or {}) if isinstance(cost_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        status, summary_resp = _post(intent_url, token, "cost.tracking.block.fetch", ((cost_hints.get("summary") or {}) if isinstance(cost_hints.get("summary"), dict) else {}).get("params") or {"project_id": project_id, "block_key": "summary"}, db_name=db_name)
        _assert_ok(status, summary_resp, "cost.tracking.block.fetch(summary)")
        summary_data = summary_resp.get("data") if isinstance(summary_resp.get("data"), dict) else {}
        summary_block = summary_data.get("block") if isinstance(summary_data.get("block"), dict) else {}
        if str(summary_data.get("block_key") or "").strip() != "summary":
            raise RuntimeError("cost summary block key mismatch")
        if str(summary_block.get("block_type") or "").strip() != "fact_summary":
            raise RuntimeError("cost summary block type mismatch")

        report["flow"] = {
            "project_id": project_id,
            "cost_action_state": str(cost_action.get("state") or ""),
            "cost_entry_keys": sorted(cost_entry.keys()),
            "summary_block_state": str(summary_block.get("state") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_execution_cost_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_execution_cost_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
