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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_consistency_guard.json"


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


def _fetch_next_actions(intent_url: str, token: str, db_name: str, project_id: int) -> dict:
    status, response = _post(
        intent_url,
        token,
        "project.execution.block.fetch",
        {"project_id": project_id, "block_key": "next_actions"},
        db_name=db_name,
    )
    _assert_ok(status, response, "project.execution.block.fetch(next_actions)")
    block = (((response.get("data") or {}).get("block")) or {})
    data = block.get("data") if isinstance(block.get("data"), dict) else {}
    actions = data.get("actions") if isinstance(data.get("actions"), list) else []
    action = next(
        (row for row in actions if isinstance(row, dict) and str(row.get("intent") or "") == "project.execution.advance"),
        None,
    )
    if not isinstance(action, dict):
        raise RuntimeError("missing project.execution.advance action")
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return {"action": action, "summary": summary}


def _assert_summary(summary: dict, *, current_state: str, open_count: int, in_progress_count: int, done_count: int, followup_count: int) -> None:
    if str(summary.get("current_state") or "") != current_state:
        raise RuntimeError(f"current_state drift: {summary}")
    if int(summary.get("task_open_count") or 0) != open_count:
        raise RuntimeError(f"task_open_count drift: {summary}")
    if int(summary.get("task_in_progress_count") or 0) != in_progress_count:
        raise RuntimeError(f"task_in_progress_count drift: {summary}")
    if int(summary.get("task_done_count") or 0) != done_count:
        raise RuntimeError(f"task_done_count drift: {summary}")
    if int(summary.get("followup_activity_count") or 0) != followup_count:
        raise RuntimeError(f"followup_activity_count drift: {summary}")
    if str(summary.get("execution_scope") or "") != "single_open_task_only":
        raise RuntimeError(f"execution scope drift: {summary}")
    if str(summary.get("consistency_state") or "") != "consistent":
        raise RuntimeError(f"consistency_state drift: {summary}")
    if str(summary.get("consistency_reason_code") or ""):
        raise RuntimeError(f"consistency_reason_code should be empty: {summary}")


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

        status, create_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P14C-CONSIST-{uuid4().hex[:8]}",
                "description": "execution consistency guard",
                "date_start": str(os.getenv("P14C_DATE_START") or "2026-03-23"),
            },
            db_name=db_name,
        )
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        first = _fetch_next_actions(intent_url, token, db_name, project_id)
        _assert_summary(first["summary"], current_state="ready", open_count=1, in_progress_count=0, done_count=0, followup_count=0)

        params = first["action"].get("params") if isinstance(first["action"].get("params"), dict) else {}
        status, first_advance = _post(intent_url, token, "project.execution.advance", params, db_name=db_name)
        _assert_ok(status, first_advance, "project.execution.advance(first)")
        first_data = first_advance.get("data") if isinstance(first_advance.get("data"), dict) else {}
        if str(first_data.get("result") or "") != "success":
            raise RuntimeError(f"first advance failed: {first_data}")

        second = _fetch_next_actions(intent_url, token, db_name, project_id)
        _assert_summary(second["summary"], current_state="in_progress", open_count=1, in_progress_count=1, done_count=0, followup_count=1)

        params = second["action"].get("params") if isinstance(second["action"].get("params"), dict) else {}
        status, second_advance = _post(intent_url, token, "project.execution.advance", params, db_name=db_name)
        _assert_ok(status, second_advance, "project.execution.advance(second)")
        second_data = second_advance.get("data") if isinstance(second_advance.get("data"), dict) else {}
        if str(second_data.get("result") or "") != "success":
            raise RuntimeError(f"second advance failed: {second_data}")

        third = _fetch_next_actions(intent_url, token, db_name, project_id)
        _assert_summary(third["summary"], current_state="done", open_count=0, in_progress_count=0, done_count=1, followup_count=0)

        report["consistency"] = {
            "project_id": project_id,
            "initial_summary": first["summary"],
            "in_progress_summary": second["summary"],
            "done_summary": third["summary"],
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_consistency_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_consistency_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
