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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_state_transition_guard.json"
ALLOWED_STATES = {"ready", "in_progress", "blocked", "done"}
ALLOWED_PAIRS = {
    ("ready", "in_progress"),
    ("in_progress", "done"),
    ("blocked", "ready"),
}


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


def _extract_action(block_resp: dict) -> dict:
    block = (((block_resp.get("data") or {}).get("block")) or {})
    actions = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("actions")) or [])
    action = next((row for row in actions if isinstance(row, dict) and str(row.get("intent") or "").strip() == "project.execution.advance"), None)
    if not isinstance(action, dict):
        raise RuntimeError("execution next_actions missing project.execution.advance")
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
        token = _extract_login_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, create_resp = _post(intent_url, token, "project.initiation.enter", {
            "name": f"P13C-STATE-{uuid4().hex[:8]}",
            "description": "execution state transition guard",
            "date_start": str(os.getenv("P13C_DATE_START") or "2026-03-22"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, next_resp = _post(intent_url, token, "project.execution.block.fetch", {"project_id": project_id, "block_key": "next_actions"}, db_name=db_name)
        _assert_ok(status, next_resp, "project.execution.block.fetch(next_actions)")
        action = _extract_action(next_resp)
        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        current_state = str(action.get("current_state") or params.get("current_state") or "")
        target_state = str(action.get("target_state") or params.get("target_state") or "")
        if target_state not in ALLOWED_STATES:
            raise RuntimeError(f"invalid target_state: {target_state!r}")
        if current_state and current_state not in ALLOWED_STATES:
            raise RuntimeError(f"invalid current_state: {current_state!r}")
        if current_state and (current_state, target_state) not in ALLOWED_PAIRS:
            raise RuntimeError(f"unexpected allowed pair: {(current_state, target_state)!r}")

        status, success_resp = _post(intent_url, token, "project.execution.advance", params, db_name=db_name)
        _assert_ok(status, success_resp, "project.execution.advance(allowed)")
        success_data = success_resp.get("data") if isinstance(success_resp.get("data"), dict) else {}
        if str(success_data.get("result") or "") != "success":
            raise RuntimeError(f"expected success result, got {success_data.get('result')!r}")
        success_from = str(success_data.get("from_state") or "")
        success_to = str(success_data.get("to_state") or "")
        if success_from not in ALLOWED_STATES:
            raise RuntimeError(f"invalid success from_state: {success_from!r}")
        if success_to not in ALLOWED_STATES:
            raise RuntimeError(f"invalid success to_state: {success_to!r}")
        if success_to != target_state:
            raise RuntimeError("to_state mismatch on legal transition")
        if (success_from, success_to) not in ALLOWED_PAIRS:
            raise RuntimeError("legal transition pair drift")
        if current_state and success_from != current_state:
            raise RuntimeError("from_state mismatch on legal transition")

        status, illegal_resp = _post(intent_url, token, "project.execution.advance", {"project_id": project_id, "target_state": "ready"}, db_name=db_name)
        _assert_ok(status, illegal_resp, "project.execution.advance(illegal)")
        illegal_data = illegal_resp.get("data") if isinstance(illegal_resp.get("data"), dict) else {}
        if str(illegal_data.get("result") or "") != "blocked":
            raise RuntimeError(f"expected blocked result for illegal transition, got {illegal_data.get('result')!r}")
        if str(illegal_data.get("from_state") or "") != success_to:
            raise RuntimeError("illegal transition from_state drift")
        if str(illegal_data.get("to_state") or "") != success_to:
            raise RuntimeError("illegal transition to_state drift")
        if not str(illegal_data.get("reason_code") or "").strip():
            raise RuntimeError("illegal transition reason_code missing")

        report["transition"] = {
            "project_id": project_id,
            "action_current_state": current_state,
            "legal_from_state": success_from,
            "legal_to_state": success_to,
            "legal_reason_code": str(success_data.get("reason_code") or ""),
            "illegal_from_state": str(illegal_data.get("from_state") or ""),
            "illegal_to_state": str(illegal_data.get("to_state") or ""),
            "illegal_reason_code": str(illegal_data.get("reason_code") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_state_transition_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_state_transition_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
