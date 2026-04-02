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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_cost_list_block_guard.json"
REQUIRED_RESPONSE_KEYS = {"project_id", "block_key", "block"}
OPTIONAL_RESPONSE_KEYS = {"degraded", "project_context"}
REQUIRED_BLOCK_KEYS = {"block_key", "block_type", "title", "state", "visibility", "data"}
OPTIONAL_BLOCK_KEYS = {"error"}
RECORD_KEYS = {"move_id", "name", "date", "state", "move_type", "partner_name", "amount", "currency_name", "description", "category_name", "category_type", "project_id", "project_name"}


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

        status, create_project = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {"name": f"FR3-COST-LIST-{uuid4().hex[:8]}", "description": "fr3 cost list guard", "date_start": "2026-03-23"},
            db_name=db_name,
        )
        _assert_ok(status, create_project, "project.initiation.enter")
        project_id = int((((create_project.get("data") or {}) if isinstance(create_project.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, form_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": "cost_entry"}, db_name=db_name)
        _assert_ok(status, form_resp, "cost.tracking.block.fetch(cost_entry)")
        form_block = (((form_resp.get("data") or {}) if isinstance(form_resp.get("data"), dict) else {}).get("block") or {})
        form_data = ((form_block.get("data") or {}) if isinstance(form_block.get("data"), dict) else {})
        form = ((form_data.get("form") or {}) if isinstance(form_data.get("form"), dict) else {})
        options = (((form.get("options") or {}) if isinstance(form.get("options"), dict) else {}).get("cost_code_id") or [])
        first_option = options[0] if isinstance(options, list) and options else {}
        cost_code_id = int((first_option.get("value") or 0) if isinstance(first_option, dict) else 0)

        status, create_cost = _post(
            intent_url,
            token,
            "cost.tracking.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "888.00",
                "description": "FR-3 list guard item",
                "cost_code_id": cost_code_id,
            },
            db_name=db_name,
        )
        _assert_ok(status, create_cost, "cost.tracking.record.create")

        status, block_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": "cost_list"}, db_name=db_name)
        _assert_ok(status, block_resp, "cost.tracking.block.fetch(cost_list)")
        data = block_resp.get("data") if isinstance(block_resp.get("data"), dict) else {}
        data_keys = set(data.keys())
        missing_response_keys = sorted(REQUIRED_RESPONSE_KEYS - data_keys)
        if missing_response_keys:
            raise RuntimeError(f"response missing required keys: {missing_response_keys}")
        unknown_response_keys = sorted(data_keys - REQUIRED_RESPONSE_KEYS - OPTIONAL_RESPONSE_KEYS)
        if unknown_response_keys:
            raise RuntimeError(f"response keys drift: {unknown_response_keys}")
        block = data.get("block") if isinstance(data.get("block"), dict) else {}
        block_keys = set(block.keys())
        missing_block_keys = sorted(REQUIRED_BLOCK_KEYS - block_keys)
        if missing_block_keys:
            raise RuntimeError(f"block missing required keys: {missing_block_keys}")
        unknown_block_keys = sorted(block_keys - REQUIRED_BLOCK_KEYS - OPTIONAL_BLOCK_KEYS)
        if unknown_block_keys:
            raise RuntimeError(f"block keys drift: {unknown_block_keys}")
        if str(block.get("block_type") or "").strip() != "record_list":
            raise RuntimeError(f"block type drift: {block.get('block_type')!r}")
        records = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("records")) or [])
        if not isinstance(records, list) or not records:
            raise RuntimeError("cost list records missing")
        first = records[0] if isinstance(records[0], dict) else {}
        if set(first.keys()) != RECORD_KEYS:
            raise RuntimeError(f"record keys drift: {sorted(first.keys())}")
        if int(first.get("project_id") or 0) != project_id:
            raise RuntimeError("project linkage mismatch")
        report["list"] = {
            "project_id": project_id,
            "record_count": len(records),
            "first_record": first,
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_cost_list_block_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_cost_list_block_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
