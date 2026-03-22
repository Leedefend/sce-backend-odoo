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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_action_contract_guard.json"

DATA_KEYS = {"result", "project_id", "reason_code", "suggested_action"}
SUGGESTED_ACTION_KEYS = {"key", "intent", "params", "reason_code"}
ALLOWED_RESULTS = {"success", "blocked"}


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

        status, create_resp = _post(intent_url, token, "project.initiation.enter", {
            "name": f"P13C-ACTION-{uuid4().hex[:8]}",
            "description": "execution action contract guard",
            "date_start": str(os.getenv("P13C_DATE_START") or "2026-03-22"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, advance_resp = _post(intent_url, token, "project.execution.advance", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, advance_resp, "project.execution.advance")
        data = advance_resp.get("data") if isinstance(advance_resp.get("data"), dict) else {}
        if set(data.keys()) != DATA_KEYS:
            raise RuntimeError(f"action data keys drift: {sorted(data.keys())}")
        if str(data.get("result") or "").strip() not in ALLOWED_RESULTS:
            raise RuntimeError(f"action result drift: {data.get('result')!r}")
        if int(data.get("project_id") or 0) != project_id:
            raise RuntimeError("action project_id mismatch")
        if not str(data.get("reason_code") or "").strip():
            raise RuntimeError("action reason_code missing")
        suggested = data.get("suggested_action") if isinstance(data.get("suggested_action"), dict) else {}
        if set(suggested.keys()) != SUGGESTED_ACTION_KEYS:
            raise RuntimeError(f"suggested_action keys drift: {sorted(suggested.keys())}")
        if not str(suggested.get("intent") or "").strip():
            raise RuntimeError("suggested_action.intent missing")
        if not isinstance(suggested.get("params"), dict):
            raise RuntimeError("suggested_action.params missing")
        if not str(suggested.get("reason_code") or "").strip():
            raise RuntimeError("suggested_action.reason_code missing")

        report["action"] = {
            "project_id": project_id,
            "result": str(data.get("result") or ""),
            "reason_code": str(data.get("reason_code") or ""),
            "suggested_action_intent": str(suggested.get("intent") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_action_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_action_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
