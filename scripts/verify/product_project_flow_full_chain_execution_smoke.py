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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_full_chain_execution_smoke.json"


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
                "name": f"P13B-EXEC-{uuid4().hex[:8]}",
                "description": "Phase 13-B/B2 full chain execution smoke",
                "date_start": str(os.getenv("P13B_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        project_id = int((((initiation_data.get("record") or {}) if isinstance(initiation_data.get("record"), dict) else {}).get("id") or 0))
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        dashboard_action = initiation_data.get("suggested_action_payload") if isinstance(initiation_data.get("suggested_action_payload"), dict) else {}
        dashboard_params = dashboard_action.get("params") if isinstance(dashboard_action.get("params"), dict) else {}
        if str(dashboard_action.get("intent") or "").strip() != "project.dashboard.enter":
            raise RuntimeError("initiation suggested action does not point to dashboard.enter")
        if int(dashboard_params.get("project_id") or 0) != project_id:
            raise RuntimeError("initiation->dashboard project_id mismatch")

        status, dashboard_resp = _post(intent_url, token, "project.dashboard.enter", dashboard_params, db_name=db_name)
        _assert_ok(status, dashboard_resp, "project.dashboard.enter")
        dashboard_entry = dashboard_resp.get("data") if isinstance(dashboard_resp.get("data"), dict) else {}
        dashboard_blocks = (((dashboard_entry.get("runtime_fetch_hints") or {}) if isinstance(dashboard_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        status, dashboard_next_actions_resp = _post(intent_url, token, "project.dashboard.block.fetch", ((dashboard_blocks.get("next_actions") or {}) if isinstance(dashboard_blocks.get("next_actions"), dict) else {}).get("params") or {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, dashboard_next_actions_resp, "project.dashboard.block.fetch(next_actions)")
        dashboard_next_actions = (((((dashboard_next_actions_resp.get("data") or {}).get("block") or {}).get("data") or {}).get("actions")) or [])
        plan_action = next((row for row in dashboard_next_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.plan_bootstrap.enter"), None)
        if not isinstance(plan_action, dict):
            raise RuntimeError("dashboard next_actions missing project.plan_bootstrap.enter")
        plan_params = plan_action.get("params") if isinstance(plan_action.get("params"), dict) else {}
        if int(plan_params.get("project_id") or 0) != project_id:
            raise RuntimeError("dashboard->plan project_id mismatch")

        status, plan_resp = _post(intent_url, token, "project.plan_bootstrap.enter", plan_params, db_name=db_name)
        _assert_ok(status, plan_resp, "project.plan_bootstrap.enter")
        plan_entry = plan_resp.get("data") if isinstance(plan_resp.get("data"), dict) else {}
        if int(plan_entry.get("project_id") or 0) != project_id:
            raise RuntimeError("plan entry project_id mismatch")

        status, plan_actions_resp = _post(intent_url, token, "project.plan_bootstrap.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, plan_actions_resp, "project.plan_bootstrap.block.fetch(next_actions)")
        plan_actions = (((((plan_actions_resp.get("data") or {}).get("block") or {}).get("data") or {}).get("actions")) or [])
        execution_action = next((row for row in plan_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.enter"), None)
        if not isinstance(execution_action, dict):
            raise RuntimeError("plan next_actions missing project.execution.enter")
        execution_params = execution_action.get("params") if isinstance(execution_action.get("params"), dict) else {}
        if int(execution_params.get("project_id") or 0) != project_id:
            raise RuntimeError("plan->execution project_id mismatch")

        status, execution_resp = _post(intent_url, token, "project.execution.enter", execution_params, db_name=db_name)
        _assert_ok(status, execution_resp, "project.execution.enter")
        execution_entry = execution_resp.get("data") if isinstance(execution_resp.get("data"), dict) else {}
        if int(execution_entry.get("project_id") or 0) != project_id:
            raise RuntimeError("execution entry project_id mismatch")
        execution_hints = (((execution_entry.get("runtime_fetch_hints") or {}) if isinstance(execution_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        execution_hint = execution_hints.get("execution_tasks") if isinstance(execution_hints.get("execution_tasks"), dict) else {}
        if str(execution_hint.get("intent") or "").strip() != "project.execution.block.fetch":
            raise RuntimeError("execution runtime hint intent mismatch")
        execution_params_runtime = execution_hint.get("params") if isinstance(execution_hint.get("params"), dict) else {}
        if int(execution_params_runtime.get("project_id") or 0) != project_id:
            raise RuntimeError("execution runtime hint project_id mismatch")

        status, execution_block_resp = _post(intent_url, token, "project.execution.block.fetch", execution_params_runtime or {"project_id": project_id, "block_key": "execution_tasks"}, db_name=db_name)
        _assert_ok(status, execution_block_resp, "project.execution.block.fetch(execution_tasks)")
        execution_block_data = execution_block_resp.get("data") if isinstance(execution_block_resp.get("data"), dict) else {}
        execution_block = execution_block_data.get("block") if isinstance(execution_block_data.get("block"), dict) else {}
        if str(execution_block_data.get("block_key") or "").strip() != "execution_tasks":
            raise RuntimeError("execution runtime block key mismatch")
        if str(execution_block.get("block_type") or "").strip() != "execution_task_list":
            raise RuntimeError("execution runtime block type mismatch")

        report["flow"] = {
            "project_id": project_id,
            "dashboard_plan_action_state": str(plan_action.get("state") or ""),
            "plan_execution_action_state": str(execution_action.get("state") or ""),
            "execution_entry_keys": sorted(execution_entry.keys()),
            "execution_block_key": str(execution_block_data.get("block_key") or ""),
            "execution_block_state": str(execution_block.get("state") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_full_chain_execution_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_full_chain_execution_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
