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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_initiation_dashboard_smoke.json"


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


def _assert_dashboard_contract_non_empty(contract: dict) -> None:
    blocks = contract.get("blocks") if isinstance(contract.get("blocks"), list) else []
    if not blocks:
        raise RuntimeError("dashboard_contract.blocks is empty")
    required = {"progress", "risks", "next_actions"}
    seen = {str(item.get("key") or "").strip() for item in blocks if isinstance(item, dict)}
    missing = sorted(required - seen)
    if missing:
        raise RuntimeError(f"dashboard_contract missing required blocks: {', '.join(missing)}")


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
        token = ((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token"))
        token = str(token or "").strip()
        if not token:
            raise RuntimeError("login token missing")

        status, init_resp = _post(intent_url, token, "system.init", {"with_preload": True, "contract_mode": "default"}, db_name=db_name)
        _assert_ok(status, init_resp, "system.init")

        status, enter_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P12C-FLOW-{uuid4().hex[:8]}",
                "description": "Phase 12-C initiation->dashboard flow smoke",
                "date_start": str(os.getenv("P12C_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, enter_resp, "project.initiation.enter")
        enter_data = enter_resp.get("data") if isinstance(enter_resp.get("data"), dict) else {}
        record = enter_data.get("record") if isinstance(enter_data.get("record"), dict) else {}
        project_id = int(record.get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        suggested = enter_data.get("suggested_action_payload") if isinstance(enter_data.get("suggested_action_payload"), dict) else {}
        intent = str(suggested.get("intent") or "").strip()
        params = suggested.get("params") if isinstance(suggested.get("params"), dict) else {}
        if intent != "project.dashboard.enter":
            raise RuntimeError(f"expected suggested intent project.dashboard.enter, got {intent!r}")
        if int(params.get("project_id") or 0) != project_id:
            raise RuntimeError("suggested_action_payload.params.project_id mismatch")

        status, dash_resp = _post(intent_url, token, intent, params, db_name=db_name)
        _assert_ok(status, dash_resp, "project.dashboard.enter")
        dash_data = dash_resp.get("data") if isinstance(dash_resp.get("data"), dict) else {}
        dash_project_id = int(dash_data.get("project_id") or 0)
        if dash_project_id != project_id:
            raise RuntimeError("project context chain broken between initiation and dashboard.enter")

        _assert_dashboard_contract_non_empty(dash_data)

        report["flow"] = {
            "project_id": project_id,
            "suggested_action_intent": intent,
            "title": str(dash_data.get("title") or ""),
            "block_keys": sorted(
                {str(item.get("key") or "").strip() for item in (dash_data.get("blocks") or []) if isinstance(item, dict)}
            ),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_initiation_dashboard_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_initiation_dashboard_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
