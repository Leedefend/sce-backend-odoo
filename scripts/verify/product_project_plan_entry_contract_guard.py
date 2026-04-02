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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_plan_entry_contract_guard.json"

REQUIRED_ENTRY_KEYS = {
    "project_id",
    "scene_key",
    "scene_label",
    "state_fallback_text",
    "title",
    "summary",
    "blocks",
    "suggested_action",
    "runtime_fetch_hints",
}
OPTIONAL_ENTRY_KEYS = {"lifecycle_hints", "scene_contract_standard_v1"}
REQUIRED_SUMMARY_KEYS = {"project_code", "manager_name", "stage_name", "date_start", "date_end"}
OPTIONAL_SUMMARY_KEYS = {
    "cost_total",
    "health_state",
    "lifecycle_state",
    "milestone",
    "partner_name",
    "payment_total",
    "progress_percent",
    "status",
}
BLOCK_KEYS = {"plan_summary_detail", "plan_tasks", "next_actions"}
BLOCK_ITEM_KEYS = {"key", "title", "state"}


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

        status, create_resp = _post(intent_url, token, "project.initiation.enter", {
            "name": f"P13B-PLAN-ENTRY-{uuid4().hex[:8]}",
            "description": "plan entry contract guard",
            "date_start": str(os.getenv("P13B_DATE_START") or "2026-03-22"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, entry_resp = _post(intent_url, token, "project.plan_bootstrap.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, entry_resp, "project.plan_bootstrap.enter")
        entry = entry_resp.get("data") if isinstance(entry_resp.get("data"), dict) else {}
        entry_keys = set(entry.keys())
        missing_entry_keys = sorted(REQUIRED_ENTRY_KEYS - entry_keys)
        if missing_entry_keys:
            raise RuntimeError(f"entry missing required keys: {missing_entry_keys}")
        unknown_entry_keys = sorted(entry_keys - REQUIRED_ENTRY_KEYS - OPTIONAL_ENTRY_KEYS)
        if unknown_entry_keys:
            raise RuntimeError(f"entry keys drift: {unknown_entry_keys}")
        if str(entry.get("scene_key") or "").strip() != "project.plan_bootstrap":
            raise RuntimeError(f"scene_key drift: {entry.get('scene_key')!r}")
        if not str(entry.get("scene_label") or "").strip():
            raise RuntimeError("scene_label missing")
        if not str(entry.get("state_fallback_text") or "").strip():
            raise RuntimeError("state_fallback_text missing")
        summary = entry.get("summary") if isinstance(entry.get("summary"), dict) else {}
        summary_keys = set(summary.keys())
        missing_summary_keys = sorted(REQUIRED_SUMMARY_KEYS - summary_keys)
        if missing_summary_keys:
            raise RuntimeError(f"entry summary missing required keys: {missing_summary_keys}")
        unknown_summary_keys = sorted(summary_keys - REQUIRED_SUMMARY_KEYS - OPTIONAL_SUMMARY_KEYS)
        if unknown_summary_keys:
            raise RuntimeError(f"entry summary keys drift: {unknown_summary_keys}")
        blocks = entry.get("blocks") if isinstance(entry.get("blocks"), list) else []
        seen_blocks = set()
        for row in blocks:
            if not isinstance(row, dict):
                raise RuntimeError("entry block row is not object")
            if set(row.keys()) != BLOCK_ITEM_KEYS:
                raise RuntimeError(f"entry block item keys drift: {sorted(row.keys())}")
            seen_blocks.add(str(row.get("key") or "").strip())
        if seen_blocks != BLOCK_KEYS:
            raise RuntimeError(f"entry block keys drift: {sorted(seen_blocks)}")
        hints = (((entry.get("runtime_fetch_hints") or {}) if isinstance(entry.get("runtime_fetch_hints"), dict) else {}).get("blocks") or {})
        if set(hints.keys()) != BLOCK_KEYS:
            raise RuntimeError(f"runtime hint block keys drift: {sorted(hints.keys())}")

        report["entry"] = {
            "project_id": project_id,
            "entry_keys": sorted(entry.keys()),
            "summary_keys": sorted(summary.keys()),
            "block_keys": sorted(seen_blocks),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_plan_entry_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_plan_entry_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
