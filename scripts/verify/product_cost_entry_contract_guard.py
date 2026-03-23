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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_cost_entry_contract_guard.json"

EXPECTED_RESULT_KEYS = {
    "project_id",
    "move_id",
    "move_name",
    "state",
    "amount",
    "date",
    "description",
    "category_name",
    "summary_hint",
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


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
    _assert_ok(status, login_resp, "login")
    token = str(((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token") or "")).strip()
    if not token:
        raise RuntimeError("login token missing")
    return token


def _create_project(intent_url: str, token: str, db_name: str) -> int:
    status, create_resp = _post(
        intent_url,
        token,
        "project.initiation.enter",
        {
            "name": f"FR3-COST-ENTRY-{uuid4().hex[:8]}",
            "description": "fr3 cost entry contract guard",
            "date_start": str(os.getenv("FR3_DATE_START") or "2026-03-23"),
        },
        db_name=db_name,
    )
    _assert_ok(status, create_resp, "project.initiation.enter")
    project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
    if project_id <= 0:
        raise RuntimeError("project id missing")
    return project_id


def _cost_code_id(intent_url: str, token: str, db_name: str, project_id: int) -> int:
    status, block_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": "cost_entry"}, db_name=db_name)
    _assert_ok(status, block_resp, "cost.tracking.block.fetch(cost_entry)")
    block = (((block_resp.get("data") or {}) if isinstance(block_resp.get("data"), dict) else {}).get("block") or {})
    form = (((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("form") or {})
    options = (((form.get("options") or {}) if isinstance(form.get("options"), dict) else {}).get("cost_code_id") or [])
    first = options[0] if isinstance(options, list) and options else {}
    return int((first.get("value") or 0) if isinstance(first, dict) else 0)


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
        token = _login(intent_url, db_name, login, password)
        project_id = _create_project(intent_url, token, db_name)
        cost_code_id = _cost_code_id(intent_url, token, db_name, project_id)
        params = {
            "project_id": project_id,
            "date": str(os.getenv("FR3_COST_DATE") or "2026-03-23"),
            "amount": "1234.56",
            "description": "FR-3 prepared cost entry",
            "cost_code_id": cost_code_id,
        }
        status, create_resp = _post(intent_url, token, "cost.tracking.record.create", params, db_name=db_name)
        _assert_ok(status, create_resp, "cost.tracking.record.create")
        data = create_resp.get("data") if isinstance(create_resp.get("data"), dict) else {}
        if set(data.keys()) != EXPECTED_RESULT_KEYS:
            raise RuntimeError(f"create result keys drift: {sorted(data.keys())}")
        if int(data.get("project_id") or 0) != project_id:
            raise RuntimeError("project_id mismatch")
        if int(data.get("move_id") or 0) <= 0:
            raise RuntimeError("move_id missing")
        if str(data.get("state") or "").strip() not in {"draft", "posted"}:
            raise RuntimeError(f"unexpected state: {data.get('state')!r}")
        report["entry"] = data
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_cost_entry_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_cost_entry_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
