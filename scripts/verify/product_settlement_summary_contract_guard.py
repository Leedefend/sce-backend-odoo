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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_settlement_summary_contract_guard.json"
EXPECTED_SUMMARY_KEYS = {
    "project_id",
    "carrier_models",
    "total_cost",
    "total_payment",
    "delta",
    "currency_name",
    "cost_record_count",
    "payment_record_count",
    "scope",
    "as_of_date",
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
                "name": f"FR5-SETTLEMENT-{uuid4().hex[:8]}",
                "description": "fr5 settlement summary contract guard",
                "date_start": str(os.getenv("FR5_DATE_START") or "2026-03-23"),
            },
            db_name=db_name,
        )
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, cost_resp = _post(
            intent_url,
            token,
            "cost.tracking.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "200.00",
                "description": "FR-5 contract guard cost",
            },
            db_name=db_name,
        )
        _assert_ok(status, cost_resp, "cost.tracking.record.create")

        status, payment_resp = _post(
            intent_url,
            token,
            "payment.record.create",
            {
                "project_id": project_id,
                "date": "2026-03-23",
                "amount": "120.00",
                "description": "FR-5 contract guard payment",
            },
            db_name=db_name,
        )
        _assert_ok(status, payment_resp, "payment.record.create")

        status, settlement_entry_resp = _post(intent_url, token, "settlement.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, settlement_entry_resp, "settlement.enter")
        settlement_entry = settlement_entry_resp.get("data") if isinstance(settlement_entry_resp.get("data"), dict) else {}
        hints = (((settlement_entry.get("runtime_fetch_hints") or {}) if isinstance(settlement_entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})

        status, summary_resp = _post(
            intent_url,
            token,
            "settlement.block.fetch",
            ((hints.get("settlement_summary") or {}) if isinstance(hints.get("settlement_summary"), dict) else {}).get("params") or {"project_id": project_id, "block_key": "settlement_summary"},
            db_name=db_name,
        )
        _assert_ok(status, summary_resp, "settlement.block.fetch")
        data = summary_resp.get("data") if isinstance(summary_resp.get("data"), dict) else {}
        block = data.get("block") if isinstance(data.get("block"), dict) else {}
        summary = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("summary")) or {})
        if set(summary.keys()) != EXPECTED_SUMMARY_KEYS:
            raise RuntimeError(f"settlement summary keys drift: {sorted(summary.keys())}")
        if float(summary.get("total_cost") or 0.0) < 200.0:
            raise RuntimeError("total_cost too small")
        if float(summary.get("total_payment") or 0.0) < 120.0:
            raise RuntimeError("total_payment too small")
        if round(float(summary.get("delta") or 0.0), 2) != round(float(summary.get("total_payment") or 0.0) - float(summary.get("total_cost") or 0.0), 2):
            raise RuntimeError("delta mismatch")
        report["summary"] = summary
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_settlement_summary_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_settlement_summary_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
