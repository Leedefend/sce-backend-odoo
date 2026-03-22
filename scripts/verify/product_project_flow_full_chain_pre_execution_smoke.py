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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_full_chain_pre_execution_smoke.json"


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
                "name": f"P13B-FULL-{uuid4().hex[:8]}",
                "description": "Phase 13-B/B1 full chain pre execution smoke",
                "date_start": str(os.getenv("P13B_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        record = initiation_data.get("record") if isinstance(initiation_data.get("record"), dict) else {}
        project_id = int(record.get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        dashboard_action = initiation_data.get("suggested_action_payload") if isinstance(initiation_data.get("suggested_action_payload"), dict) else {}
        dashboard_params = dashboard_action.get("params") if isinstance(dashboard_action.get("params"), dict) else {}
        if str(dashboard_action.get("intent") or "").strip() != "project.dashboard.enter":
            raise RuntimeError("initiation suggested action does not point to project.dashboard.enter")
        if int(dashboard_params.get("project_id") or 0) != project_id:
            raise RuntimeError("initiation->dashboard project_id mismatch")

        status, dashboard_resp = _post(intent_url, token, "project.dashboard.enter", dashboard_params, db_name=db_name)
        _assert_ok(status, dashboard_resp, "project.dashboard.enter")
        dashboard_entry = dashboard_resp.get("data") if isinstance(dashboard_resp.get("data"), dict) else {}
        dashboard_hints = (((dashboard_entry.get("runtime_fetch_hints") or {}) if isinstance(dashboard_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        next_actions_hint = dashboard_hints.get("next_actions") if isinstance(dashboard_hints.get("next_actions"), dict) else {}

        status, dash_actions_resp = _post(
            intent_url,
            token,
            str(next_actions_hint.get("intent") or "project.dashboard.block.fetch"),
            next_actions_hint.get("params") if isinstance(next_actions_hint.get("params"), dict) else {"project_id": project_id, "block_key": "next_actions"},
            db_name=db_name,
        )
        _assert_ok(status, dash_actions_resp, "project.dashboard.block.fetch(next_actions)")
        dash_actions = (((((dash_actions_resp.get("data") or {}).get("block") or {}).get("data") or {}).get("actions")) or [])
        plan_action = next((row for row in dash_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.plan_bootstrap.enter"), None)
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
        plan_hints = (((plan_entry.get("runtime_fetch_hints") or {}) if isinstance(plan_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        if sorted(plan_hints.keys()) != ["next_actions", "plan_summary_detail", "plan_tasks"]:
            raise RuntimeError(f"plan runtime hints drift: {sorted(plan_hints.keys())}")

        status, plan_actions_resp = _post(
            intent_url,
            token,
            "project.plan_bootstrap.block.fetch",
            {"project_id": project_id, "block_key": "next_actions"},
            db_name=db_name,
        )
        _assert_ok(status, plan_actions_resp, "project.plan_bootstrap.block.fetch(next_actions)")
        plan_actions_block = (((plan_actions_resp.get("data") or {}).get("block")) or {})
        plan_actions = ((((plan_actions_block.get("data") or {}) if isinstance(plan_actions_block.get("data"), dict) else {}).get("actions")) or [])
        execution_action = next((row for row in plan_actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.enter"), None)
        if not isinstance(execution_action, dict):
            raise RuntimeError("plan next_actions missing project.execution.enter")
        execution_params = execution_action.get("params") if isinstance(execution_action.get("params"), dict) else {}
        if int(execution_params.get("project_id") or 0) != project_id:
            raise RuntimeError("plan->execution project_id mismatch")

        status, execution_resp = _post(intent_url, token, "project.execution.enter", execution_params, db_name=db_name)
        _assert_ok(status, execution_resp, "project.execution.enter")
        execution_data = execution_resp.get("data") if isinstance(execution_resp.get("data"), dict) else {}
        if int(execution_data.get("project_id") or 0) != project_id:
            raise RuntimeError("execution enter project_id mismatch")

        report["flow"] = {
            "project_id": project_id,
            "dashboard_plan_action_state": str(plan_action.get("state") or ""),
            "plan_execution_action_state": str(execution_action.get("state") or ""),
            "plan_execution_reason_code": str(execution_action.get("reason_code") or ""),
            "execution_state": str(execution_data.get("state") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_full_chain_pre_execution_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_full_chain_pre_execution_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
