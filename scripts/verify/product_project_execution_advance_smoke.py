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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_advance_smoke.json"


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


def _fetch_action(intent_url: str, token: str, db_name: str, project_id: int):
    status, execution_resp = _post(intent_url, token, "project.execution.enter", {"project_id": project_id}, db_name=db_name)
    _assert_ok(status, execution_resp, "project.execution.enter")
    execution_entry = execution_resp.get("data") if isinstance(execution_resp.get("data"), dict) else {}
    hints = (((execution_entry.get("runtime_fetch_hints") or {}) if isinstance(execution_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
    next_action_hint = hints.get("next_actions") if isinstance(hints.get("next_actions"), dict) else {}
    status, actions_resp = _post(
        intent_url,
        token,
        str(next_action_hint.get("intent") or "project.execution.block.fetch"),
        next_action_hint.get("params") if isinstance(next_action_hint.get("params"), dict) else {"project_id": project_id, "block_key": "next_actions"},
        db_name=db_name,
    )
    _assert_ok(status, actions_resp, "project.execution.block.fetch(next_actions)")
    block = (((actions_resp.get("data") or {}).get("block")) or {})
    actions = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("actions")) or [])
    advance_action = next((row for row in actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.advance"), None)
    if not isinstance(advance_action, dict):
        raise RuntimeError("execution next_actions missing project.execution.advance")
    return advance_action


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
                "name": f"P13C-ADV-{uuid4().hex[:8]}",
                "description": "Phase 13-C/C1 execution advance smoke",
                "date_start": str(os.getenv("P13C_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        project_id = int((((initiation_data.get("record") or {}) if isinstance(initiation_data.get("record"), dict) else {}).get("id") or 0))
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        status, dashboard_resp = _post(intent_url, token, "project.dashboard.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, dashboard_resp, "project.dashboard.enter")
        status, dashboard_next_resp = _post(intent_url, token, "project.dashboard.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, dashboard_next_resp, "project.dashboard.block.fetch(next_actions)")
        dashboard_actions = (((((dashboard_next_resp.get("data") or {}).get("block") or {}).get("data") or {}).get("actions")) or [])
        if not any(isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.plan_bootstrap.enter" for row in dashboard_actions):
            raise RuntimeError("dashboard next_actions missing project.plan_bootstrap.enter")

        status, plan_resp = _post(intent_url, token, "project.plan_bootstrap.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, plan_resp, "project.plan_bootstrap.enter")
        status, plan_next_resp = _post(intent_url, token, "project.plan_bootstrap.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, plan_next_resp, "project.plan_bootstrap.block.fetch(next_actions)")
        plan_actions = (((((plan_next_resp.get("data") or {}).get("block") or {}).get("data") or {}).get("actions")) or [])
        if not any(isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.enter" for row in plan_actions):
            raise RuntimeError("plan next_actions missing project.execution.enter")

        advance_action = _fetch_action(intent_url, token, db_name, project_id)
        advance_params = advance_action.get("params") if isinstance(advance_action.get("params"), dict) else {}
        if int(advance_params.get("project_id") or 0) != project_id:
            raise RuntimeError("execution advance project_id mismatch")

        status, advance_resp = _post(intent_url, token, "project.execution.advance", advance_params, db_name=db_name)
        _assert_ok(status, advance_resp, "project.execution.advance")
        advance_data = advance_resp.get("data") if isinstance(advance_resp.get("data"), dict) else {}
        result = str(advance_data.get("result") or "").strip()
        if result not in {"success", "blocked"}:
            raise RuntimeError(f"unexpected advance result: {result!r}")
        if int(advance_data.get("project_id") or 0) != project_id:
            raise RuntimeError("advance result project_id mismatch")
        if not str(advance_data.get("reason_code") or "").strip():
            raise RuntimeError("advance result reason_code missing")
        suggested = advance_data.get("suggested_action") if isinstance(advance_data.get("suggested_action"), dict) else {}
        if not str(suggested.get("intent") or "").strip():
            raise RuntimeError("advance suggested_action.intent missing")

        report["advance"] = {
            "project_id": project_id,
            "action_state": str(advance_action.get("state") or ""),
            "action_reason_code": str(advance_action.get("reason_code") or ""),
            "result": result,
            "result_reason_code": str(advance_data.get("reason_code") or ""),
            "suggested_action_intent": str(suggested.get("intent") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_advance_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_advance_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
