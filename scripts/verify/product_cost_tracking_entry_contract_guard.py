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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_cost_tracking_entry_contract_guard.json"

ENTRY_KEYS = {
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
SUMMARY_KEYS = {"project_code", "manager_name", "stage_name", "posted_move_count", "posted_cost_amount"}
BLOCK_KEYS = {"summary", "recent_moves", "next_actions"}
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
            "name": f"P17A-COST-ENTRY-{uuid4().hex[:8]}",
            "description": "cost tracking entry contract guard",
            "date_start": str(os.getenv("P17A_DATE_START") or "2026-03-23"),
        }, db_name=db_name)
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        status, entry_resp = _post(intent_url, token, "cost.tracking.enter", {"project_id": project_id}, db_name=db_name)
        _assert_ok(status, entry_resp, "cost.tracking.enter")
        entry = entry_resp.get("data") if isinstance(entry_resp.get("data"), dict) else {}
        if set(entry.keys()) != ENTRY_KEYS:
            raise RuntimeError(f"entry keys drift: {sorted(entry.keys())}")
        if str(entry.get("scene_key") or "").strip() != "cost.tracking":
            raise RuntimeError(f"scene_key drift: {entry.get('scene_key')!r}")
        summary = entry.get("summary") if isinstance(entry.get("summary"), dict) else {}
        if set(summary.keys()) != SUMMARY_KEYS:
            raise RuntimeError(f"summary keys drift: {sorted(summary.keys())}")
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
        print("[product_cost_tracking_entry_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_cost_tracking_entry_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
