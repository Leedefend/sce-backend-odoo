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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_state_smoke.json"


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


def _actions_from_block(response: dict) -> list:
    block = (((response.get("data") or {}).get("block")) or {})
    return ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("actions")) or [])


def _advance_action(actions: list) -> dict:
    action = next((row for row in actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.advance"), None)
    if not isinstance(action, dict):
        raise RuntimeError("missing project.execution.advance action")
    return action


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
                "name": f"P13C-STATE-SMOKE-{uuid4().hex[:8]}",
                "description": "Phase 13-C/C2 execution state smoke",
                "date_start": str(os.getenv("P13C_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        project_id = int((((initiation_data.get("record") or {}) if isinstance(initiation_data.get("record"), dict) else {}).get("id") or 0))
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        dashboard_action = initiation_data.get("suggested_action_payload") if isinstance(initiation_data.get("suggested_action_payload"), dict) else {}
        if str(dashboard_action.get("intent") or "") != "project.dashboard.enter":
            raise RuntimeError("initiation suggested_action does not point to project.dashboard.enter")

        status, dashboard_next = _post(intent_url, token, "project.dashboard.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, dashboard_next, "project.dashboard.block.fetch(next_actions)")
        dashboard_actions = _actions_from_block(dashboard_next)
        plan_action = next((row for row in dashboard_actions if isinstance(row, dict) and str(row.get("intent") or "") == "project.plan_bootstrap.enter"), None)
        execution_action = next((row for row in dashboard_actions if isinstance(row, dict) and str(row.get("intent") or "") == "project.execution.enter"), None)
        if not isinstance(plan_action, dict) and not isinstance(execution_action, dict):
            raise RuntimeError("dashboard next_actions missing project.plan_bootstrap.enter/project.execution.enter")

        if isinstance(plan_action, dict):
            status, plan_next = _post(intent_url, token, "project.plan_bootstrap.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
            _assert_ok(status, plan_next, "project.plan_bootstrap.block.fetch(next_actions)")
            plan_actions = _actions_from_block(plan_next)
            execution_action = next((row for row in plan_actions if isinstance(row, dict) and str(row.get("intent") or "") == "project.execution.enter"), None)
            if not isinstance(execution_action, dict):
                raise RuntimeError("plan next_actions missing project.execution.enter")

        status, execution_entry = _post(intent_url, token, "project.execution.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, execution_entry, "project.execution.enter")

        status, execution_next = _post(intent_url, token, "project.execution.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, execution_next, "project.execution.block.fetch(next_actions)[before]")
        first_action = _advance_action(_actions_from_block(execution_next))
        first_params = first_action.get("params") if isinstance(first_action.get("params"), dict) else {}
        if int(first_params.get("project_id") or 0) != project_id:
            raise RuntimeError("execution next_actions project_id mismatch")

        status, first_advance = _post(intent_url, token, "project.execution.advance", first_params, db_name=db_name)
        _assert_ok(status, first_advance, "project.execution.advance(first)")
        first_data = first_advance.get("data") if isinstance(first_advance.get("data"), dict) else {}
        if str(first_data.get("result") or "") != "success":
            raise RuntimeError("first execution advance did not change state")
        if str(first_data.get("from_state") or "") != "ready" or str(first_data.get("to_state") or "") != "in_progress":
            raise RuntimeError(f"unexpected first transition: {first_data}")

        status, execution_next_2 = _post(intent_url, token, "project.execution.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, execution_next_2, "project.execution.block.fetch(next_actions)[after]")
        second_action = _advance_action(_actions_from_block(execution_next_2))
        second_params = second_action.get("params") if isinstance(second_action.get("params"), dict) else {}
        if str(second_action.get("intent") or "").strip() != "project.execution.advance":
            raise RuntimeError(f"execution next_actions intent drift: {second_action}")
        if str(second_params.get("target_state") or "").strip() != "done":
            raise RuntimeError(f"execution next_actions did not target done after first advance: {second_action}")
        if str(second_action.get("reason_code") or "").strip() not in {"EXECUTION_READY_TO_COMPLETE", "EXECUTION_CAN_COMPLETE"}:
            raise RuntimeError(f"execution next_actions reason_code drift after first advance: {second_action}")

        status, second_advance = _post(intent_url, token, "project.execution.advance", second_params, db_name=db_name)
        _assert_ok(status, second_advance, "project.execution.advance(second)")
        second_data = second_advance.get("data") if isinstance(second_advance.get("data"), dict) else {}
        if str(second_data.get("result") or "") != "success":
            raise RuntimeError("second execution advance did not complete state")
        if str(second_data.get("from_state") or "") != "in_progress" or str(second_data.get("to_state") or "") != "done":
            raise RuntimeError(f"unexpected second transition: {second_data}")

        status, execution_next_3 = _post(intent_url, token, "project.execution.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, execution_next_3, "project.execution.block.fetch(next_actions)[done]")
        third_action = _advance_action(_actions_from_block(execution_next_3))
        if str(third_action.get("state") or "") != "blocked":
            raise RuntimeError("done state next_actions should be blocked")
        if str(third_action.get("reason_code") or "") != "EXECUTION_ALREADY_DONE":
            raise RuntimeError("done state reason_code drift")

        report["flow"] = {
            "project_id": project_id,
            "first_transition": [str(first_data.get("from_state") or ""), str(first_data.get("to_state") or "")],
            "second_transition": [str(second_data.get("from_state") or ""), str(second_data.get("to_state") or "")],
            "done_action_state": str(third_action.get("state") or ""),
            "done_action_reason_code": str(third_action.get("reason_code") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_state_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_state_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
