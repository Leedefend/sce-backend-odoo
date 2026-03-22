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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_flow_dashboard_plan_smoke.json"


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


def _assert_plan_entry_shape(entry: dict, project_id: int) -> None:
    allowed = {"project_id", "title", "summary", "blocks", "suggested_action", "runtime_fetch_hints"}
    keys = set(entry.keys())
    extra = sorted(keys - allowed)
    if extra:
        raise RuntimeError(f"plan entry has extra keys: {', '.join(extra)}")
    if int(entry.get("project_id") or 0) != project_id:
        raise RuntimeError("plan entry project_id mismatch")
    blocks = entry.get("blocks") if isinstance(entry.get("blocks"), list) else []
    block_keys = {str(item.get("key") or "").strip() for item in blocks if isinstance(item, dict)}
    if "plan_summary_detail" not in block_keys:
        raise RuntimeError("plan entry missing plan_summary_detail block")
    runtime_fetch_hints = entry.get("runtime_fetch_hints") if isinstance(entry.get("runtime_fetch_hints"), dict) else {}
    block_hints = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
    hint = block_hints.get("plan_summary_detail") if isinstance(block_hints.get("plan_summary_detail"), dict) else {}
    if str(hint.get("intent") or "").strip() != "project.plan_bootstrap.block.fetch":
        raise RuntimeError("plan runtime hint intent mismatch")
    params = hint.get("params") if isinstance(hint.get("params"), dict) else {}
    if int(params.get("project_id") or 0) != project_id:
        raise RuntimeError("plan runtime hint project_id mismatch")
    if str(params.get("block_key") or "").strip() != "plan_summary_detail":
        raise RuntimeError("plan runtime hint block_key mismatch")


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

        status, initiation_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P13A-PLAN-{uuid4().hex[:8]}",
                "description": "Phase 13-A dashboard->plan flow smoke",
                "date_start": str(os.getenv("P13A_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, initiation_resp, "project.initiation.enter")
        initiation_data = initiation_resp.get("data") if isinstance(initiation_resp.get("data"), dict) else {}
        record = initiation_data.get("record") if isinstance(initiation_data.get("record"), dict) else {}
        project_id = int(record.get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project.initiation.enter missing record.id")

        dashboard_action = initiation_data.get("suggested_action_payload") if isinstance(initiation_data.get("suggested_action_payload"), dict) else {}
        if str(dashboard_action.get("intent") or "").strip() != "project.dashboard.enter":
            raise RuntimeError("initiation suggested action does not point to project.dashboard.enter")
        dashboard_params = dashboard_action.get("params") if isinstance(dashboard_action.get("params"), dict) else {}
        if int(dashboard_params.get("project_id") or 0) != project_id:
            raise RuntimeError("initiation->dashboard project_id mismatch")

        status, dashboard_resp = _post(intent_url, token, "project.dashboard.enter", dashboard_params, db_name=db_name)
        _assert_ok(status, dashboard_resp, "project.dashboard.enter")
        dashboard_entry = dashboard_resp.get("data") if isinstance(dashboard_resp.get("data"), dict) else {}
        dashboard_hints = dashboard_entry.get("runtime_fetch_hints") if isinstance(dashboard_entry.get("runtime_fetch_hints"), dict) else {}
        dashboard_blocks = dashboard_hints.get("blocks") if isinstance(dashboard_hints.get("blocks"), dict) else {}
        next_actions_hint = dashboard_blocks.get("next_actions") if isinstance(dashboard_blocks.get("next_actions"), dict) else {}

        status, next_actions_resp = _post(
            intent_url,
            token,
            str(next_actions_hint.get("intent") or "project.dashboard.block.fetch"),
            next_actions_hint.get("params") if isinstance(next_actions_hint.get("params"), dict) else {"project_id": project_id, "block_key": "next_actions"},
            db_name=db_name,
        )
        _assert_ok(status, next_actions_resp, "project.dashboard.block.fetch(next_actions)")
        next_actions_data = next_actions_resp.get("data") if isinstance(next_actions_resp.get("data"), dict) else {}
        next_actions_block = next_actions_data.get("block") if isinstance(next_actions_data.get("block"), dict) else {}
        next_actions_payload = next_actions_block.get("data") if isinstance(next_actions_block.get("data"), dict) else {}
        actions = next_actions_payload.get("actions") if isinstance(next_actions_payload.get("actions"), list) else []

        plan_action = None
        for item in actions:
            if not isinstance(item, dict):
                continue
            if str(item.get("intent") or "").strip() == "project.plan_bootstrap.enter":
                plan_action = item
                break
        if not isinstance(plan_action, dict):
            raise RuntimeError("dashboard next_actions missing project.plan_bootstrap.enter")
        plan_params = plan_action.get("params") if isinstance(plan_action.get("params"), dict) else {}
        if int(plan_params.get("project_id") or 0) != project_id:
            raise RuntimeError("dashboard->plan project_id mismatch")

        status, plan_enter_resp = _post(intent_url, token, "project.plan_bootstrap.enter", plan_params, db_name=db_name)
        _assert_ok(status, plan_enter_resp, "project.plan_bootstrap.enter")
        plan_entry = plan_enter_resp.get("data") if isinstance(plan_enter_resp.get("data"), dict) else {}
        _assert_plan_entry_shape(plan_entry, project_id)

        plan_hints = plan_entry.get("runtime_fetch_hints") if isinstance(plan_entry.get("runtime_fetch_hints"), dict) else {}
        plan_blocks = plan_hints.get("blocks") if isinstance(plan_hints.get("blocks"), dict) else {}
        summary_hint = plan_blocks.get("plan_summary_detail") if isinstance(plan_blocks.get("plan_summary_detail"), dict) else {}
        status, plan_block_resp = _post(
            intent_url,
            token,
            str(summary_hint.get("intent") or "project.plan_bootstrap.block.fetch"),
            summary_hint.get("params") if isinstance(summary_hint.get("params"), dict) else {"project_id": project_id, "block_key": "plan_summary_detail"},
            db_name=db_name,
        )
        _assert_ok(status, plan_block_resp, "project.plan_bootstrap.block.fetch(plan_summary_detail)")
        plan_block_data = plan_block_resp.get("data") if isinstance(plan_block_resp.get("data"), dict) else {}
        plan_block = plan_block_data.get("block") if isinstance(plan_block_data.get("block"), dict) else {}
        if int(plan_block_data.get("project_id") or 0) != project_id:
            raise RuntimeError("plan runtime block project_id mismatch")
        if str(plan_block_data.get("block_key") or "").strip() != "plan_summary_detail":
            raise RuntimeError("plan runtime block key mismatch")
        if str(plan_block.get("block_type") or "").strip() != "plan_summary_detail":
            raise RuntimeError("plan runtime block type mismatch")

        report["flow"] = {
            "project_id": project_id,
            "dashboard_action_intent": str(plan_action.get("intent") or ""),
            "dashboard_action_state": str(plan_action.get("state") or ""),
            "plan_entry_keys": sorted(plan_entry.keys()),
            "plan_block_key": str(plan_block_data.get("block_key") or ""),
            "plan_block_state": str(plan_block.get("state") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_flow_dashboard_plan_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_flow_dashboard_plan_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
