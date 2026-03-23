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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_payment_list_block_guard.json"
RESPONSE_KEYS = {"project_id", "block_key", "block", "degraded"}
BLOCK_KEYS = {"block_key", "block_type", "title", "state", "visibility", "data", "error"}
RECORD_KEYS = {"payment_request_id", "name", "date", "state", "type", "amount", "currency_name", "description", "partner_name", "project_id", "project_name"}


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

        status, create_project = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {"name": f"FR4-PAYMENT-LIST-{uuid4().hex[:8]}", "description": "fr4 payment list guard", "date_start": "2026-03-23"},
            db_name=db_name,
        )
        _assert_ok(status, create_project, "project.initiation.enter")
        project_id = int((((create_project.get("data") or {}) if isinstance(create_project.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, create_payment = _post(
            intent_url,
            token,
            "payment.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "999.00",
                "description": "FR-4 list guard item",
            },
            db_name=db_name,
        )
        _assert_ok(status, create_payment, "payment.record.create")

        status, block_resp = _post(intent_url, token, "payment.block.fetch", {"project_id": project_id, "block_key": "payment_list"}, db_name=db_name)
        _assert_ok(status, block_resp, "payment.block.fetch(payment_list)")
        data = block_resp.get("data") if isinstance(block_resp.get("data"), dict) else {}
        if set(data.keys()) != RESPONSE_KEYS:
            raise RuntimeError(f"response keys drift: {sorted(data.keys())}")
        block = data.get("block") if isinstance(data.get("block"), dict) else {}
        if set(block.keys()) != BLOCK_KEYS:
            raise RuntimeError(f"block keys drift: {sorted(block.keys())}")
        if str(block.get("block_type") or "").strip() != "record_list":
            raise RuntimeError(f"block type drift: {block.get('block_type')!r}")
        records = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("records")) or [])
        if not isinstance(records, list) or not records:
            raise RuntimeError("payment list records missing")
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
        print("[product_payment_list_block_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_payment_list_block_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
