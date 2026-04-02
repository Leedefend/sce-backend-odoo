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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_payment_summary_block_guard.json"
REQUIRED_SUMMARY_KEYS = {
    "project_id",
    "carrier_model",
    "total_payment_amount",
    "record_count",
    "draft_record_count",
    "approved_record_count",
    "currency_name",
    "scope",
    "latest_request_date",
}
OPTIONAL_SUMMARY_KEYS = {
    "executed_payment_amount",
    "executed_record_count",
    "latest_paid_at",
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
            {"name": f"FR4-PAYMENT-SUM-{uuid4().hex[:8]}", "description": "fr4 payment summary guard", "date_start": "2026-03-23"},
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
                "amount": "654.32",
                "description": "FR-4 summary guard item",
            },
            db_name=db_name,
        )
        _assert_ok(status, create_payment, "payment.record.create")

        status, summary_resp = _post(intent_url, token, "payment.block.fetch", {"project_id": project_id, "block_key": "payment_summary"}, db_name=db_name)
        _assert_ok(status, summary_resp, "payment.block.fetch(payment_summary)")
        data = summary_resp.get("data") if isinstance(summary_resp.get("data"), dict) else {}
        block = data.get("block") if isinstance(data.get("block"), dict) else {}
        if str(data.get("block_key") or "").strip() != "payment_summary":
            raise RuntimeError("payment summary block key mismatch")
        if str(block.get("block_type") or "").strip() != "fact_summary":
            raise RuntimeError("payment summary block type mismatch")
        summary = ((((block.get("data") or {}) if isinstance(block.get("data"), dict) else {}).get("summary")) or {})
        summary_keys = set(summary.keys())
        missing_summary_keys = sorted(REQUIRED_SUMMARY_KEYS - summary_keys)
        if missing_summary_keys:
            raise RuntimeError(f"summary missing required keys: {missing_summary_keys}")
        unknown_summary_keys = sorted(summary_keys - REQUIRED_SUMMARY_KEYS - OPTIONAL_SUMMARY_KEYS)
        if unknown_summary_keys:
            raise RuntimeError(f"summary keys drift: {unknown_summary_keys}")
        if float(summary.get("total_payment_amount") or 0.0) < 654.32:
            raise RuntimeError("payment summary total too small")
        report["summary"] = summary
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_payment_summary_block_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_payment_summary_block_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
