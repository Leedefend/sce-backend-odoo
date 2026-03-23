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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_cost_summary_block_guard.json"
SUMMARY_KEYS = {"project_id", "carrier_model", "total_cost_amount", "record_count", "draft_record_count", "posted_record_count", "currency_name", "scope", "latest_move_date"}


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
            {"name": f"FR3-COST-SUMMARY-{uuid4().hex[:8]}", "description": "fr3 cost summary guard", "date_start": "2026-03-23"},
            db_name=db_name,
        )
        _assert_ok(status, create_project, "project.initiation.enter")
        project_id = int((((create_project.get("data") or {}) if isinstance(create_project.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, entry_block_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": "cost_entry"}, db_name=db_name)
        _assert_ok(status, entry_block_resp, "cost.tracking.block.fetch(cost_entry)")
        entry_data = entry_block_resp.get("data") if isinstance(entry_block_resp.get("data"), dict) else {}
        entry_block = entry_data.get("block") if isinstance(entry_data.get("block"), dict) else {}
        entry_block_data = entry_block.get("data") if isinstance(entry_block.get("data"), dict) else {}
        form = entry_block_data.get("form") if isinstance(entry_block_data.get("form"), dict) else {}
        options = (((form.get("options") or {}) if isinstance(form.get("options"), dict) else {}).get("cost_code_id") or [])
        first_option = options[0] if isinstance(options, list) and options else {}
        cost_code_id = int((first_option.get("value") or 0) if isinstance(first_option, dict) else 0)

        for amount, desc in (("500.00", "FR-3 summary guard A"), ("120.50", "FR-3 summary guard B")):
            status, create_cost = _post(
                intent_url,
                token,
                "cost.tracking.record.create",
                {"project_id": project_id, "date": "2026-03-23", "amount": amount, "description": desc, "cost_code_id": cost_code_id},
                db_name=db_name,
            )
            _assert_ok(status, create_cost, f"cost.tracking.record.create({desc})")

        status, summary_resp = _post(intent_url, token, "cost.tracking.block.fetch", {"project_id": project_id, "block_key": "cost_summary"}, db_name=db_name)
        _assert_ok(status, summary_resp, "cost.tracking.block.fetch(cost_summary)")
        block = (((summary_resp.get("data") or {}) if isinstance(summary_resp.get("data"), dict) else {}).get("block") or {})
        summary = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("summary")) or {})
        if set(summary.keys()) != SUMMARY_KEYS:
            raise RuntimeError(f"summary keys drift: {sorted(summary.keys())}")
        if float(summary.get("total_cost_amount") or 0.0) < 620.5:
            raise RuntimeError(f"unexpected total_cost_amount: {summary.get('total_cost_amount')!r}")
        if int(summary.get("record_count") or 0) < 2:
            raise RuntimeError(f"unexpected record_count: {summary.get('record_count')!r}")
        report["summary"] = summary
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_cost_summary_block_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_cost_summary_block_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
