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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_execution_settlement_smoke.json"


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
                "name": f"FR5-EXEC-SETTLE-{uuid4().hex[:8]}",
                "description": "FR-5 execution to settlement smoke",
                "date_start": str(os.getenv("FR5_DATE_START") or "2026-03-23"),
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
        execution_actions = ((((execution_next_block.get("data") or {}) if isinstance(execution_next_block.get("data"), dict) else {}).get("actions")) or [])
        settlement_action = next((row for row in execution_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "settlement.enter"), None)
        if not isinstance(settlement_action, dict):
            raise RuntimeError("execution next_actions missing settlement.enter")

        status, cost_resp = _post(
            intent_url,
            token,
            "cost.tracking.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "456.00",
                "description": "FR-5 execution settlement cost",
            },
            db_name=db_name,
        )
        _assert_ok(status, cost_resp, "cost.tracking.record.create")

        status, payment_resp = _post(
            intent_url,
            token,
            "payment.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "123.00",
                "description": "FR-5 execution settlement payment",
            },
            db_name=db_name,
        )
        _assert_ok(status, payment_resp, "payment.record.create")

        status, settlement_entry_resp = _post(intent_url, token, "settlement.enter", settlement_action.get("params") or {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, settlement_entry_resp, "settlement.enter")
        settlement_entry = settlement_entry_resp.get("data") if isinstance(settlement_entry_resp.get("data"), dict) else {}
        if str(settlement_entry.get("scene_key") or "").strip() != "settlement":
            raise RuntimeError("settlement scene_key mismatch")
        settlement_hints = (((settlement_entry.get("runtime_fetch_hints") or {}) if isinstance(settlement_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})

        status, summary_resp = _post(
            intent_url,
            token,
            "settlement.block.fetch",
            ((settlement_hints.get("settlement_summary") or {}) if isinstance(settlement_hints.get("settlement_summary"), dict) else {}).get("params") or {"project_id": project_id, "block_key": "settlement_summary"},
            db_name=db_name,
        )
        _assert_ok(status, summary_resp, "settlement.block.fetch(settlement_summary)")
        summary_data = summary_resp.get("data") if isinstance(summary_resp.get("data"), dict) else {}
        block = summary_data.get("block") if isinstance(summary_data.get("block"), dict) else {}
        if str(summary_data.get("block_key") or "").strip() != "settlement_summary":
            raise RuntimeError("settlement block key mismatch")
        if str(block.get("block_type") or "").strip() != "fact_summary":
            raise RuntimeError("settlement block type mismatch")
        summary = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("summary")) or {})
        if float(summary.get("total_cost") or 0.0) < 456.0:
            raise RuntimeError("settlement total_cost too small")
        if float(summary.get("total_payment") or 0.0) < 123.0:
            raise RuntimeError("settlement total_payment too small")

        report["flow"] = {
            "project_id": project_id,
            "settlement_action_state": str(settlement_action.get("state") or ""),
            "settlement_entry_keys": sorted(settlement_entry.keys()),
            "summary_block_state": str(block.get("state") or ""),
            "delta": float(summary.get("delta") or 0.0),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_execution_settlement_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_execution_settlement_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
