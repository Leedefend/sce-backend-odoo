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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_dashboard_flow_smoke.json"


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


def _assert_entry_shape(entry: dict, project_id: int) -> None:
    allowed = {"project_id", "title", "summary", "blocks", "suggested_action", "runtime_fetch_hints"}
    keys = set(entry.keys())
    extra = sorted(keys - allowed)
    if extra:
        raise RuntimeError(f"dashboard entry has extra keys: {', '.join(extra)}")
    if int(entry.get("project_id") or 0) != project_id:
        raise RuntimeError("dashboard entry project_id mismatch")
    blocks = entry.get("blocks") if isinstance(entry.get("blocks"), list) else []
    block_keys = {str(item.get("key") or "").strip() for item in blocks if isinstance(item, dict)}
    missing = sorted({"progress", "risks", "next_actions"} - block_keys)
    if missing:
        raise RuntimeError(f"dashboard entry missing blocks: {', '.join(missing)}")
    runtime_fetch_hints = entry.get("runtime_fetch_hints") if isinstance(entry.get("runtime_fetch_hints"), dict) else {}
    hints = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
    if not hints:
        raise RuntimeError("dashboard entry missing runtime_fetch_hints.blocks")
    for block_key in ("progress", "risks", "next_actions"):
        hint = hints.get(block_key) if isinstance(hints.get(block_key), dict) else {}
        if str(hint.get("intent") or "").strip() != "project.dashboard.block.fetch":
            raise RuntimeError(f"runtime hint intent mismatch for {block_key}")
        params = hint.get("params") if isinstance(hint.get("params"), dict) else {}
        if int(params.get("project_id") or 0) != project_id:
            raise RuntimeError(f"runtime hint project_id mismatch for {block_key}")
        if str(params.get("block_key") or "").strip() != block_key:
            raise RuntimeError(f"runtime hint block_key mismatch for {block_key}")


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

        status, enter_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P12E-DASH-{uuid4().hex[:8]}",
                "description": "Phase 12-E project dashboard flow smoke",
                "date_start": str(os.getenv("P12E_DATE_START") or "2026-03-22"),
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
        suggested_intent = str(suggested.get("intent") or "").strip()
        suggested_params = suggested.get("params") if isinstance(suggested.get("params"), dict) else {}
        if suggested_intent != "project.dashboard.enter":
            raise RuntimeError(f"expected suggested intent project.dashboard.enter, got {suggested_intent!r}")
        if int(suggested_params.get("project_id") or 0) != project_id:
            raise RuntimeError("suggested_action_payload.params.project_id mismatch")

        status, dash_resp = _post(intent_url, token, suggested_intent, suggested_params, db_name=db_name)
        _assert_ok(status, dash_resp, "project.dashboard.enter")
        dash_entry = dash_resp.get("data") if isinstance(dash_resp.get("data"), dict) else {}
        _assert_entry_shape(dash_entry, project_id)

        runtime_fetch_hints = dash_entry.get("runtime_fetch_hints") if isinstance(dash_entry.get("runtime_fetch_hints"), dict) else {}
        block_hints = runtime_fetch_hints.get("blocks") if isinstance(runtime_fetch_hints.get("blocks"), dict) else {}
        progress_hint = block_hints.get("progress") if isinstance(block_hints.get("progress"), dict) else {}
        status, progress_resp = _post(
            intent_url,
            token,
            str(progress_hint.get("intent") or "project.dashboard.block.fetch"),
            progress_hint.get("params") if isinstance(progress_hint.get("params"), dict) else {"project_id": project_id, "block_key": "progress"},
            db_name=db_name,
        )
        _assert_ok(status, progress_resp, "project.dashboard.block.fetch(progress)")
        progress_data = progress_resp.get("data") if isinstance(progress_resp.get("data"), dict) else {}
        if int(progress_data.get("project_id") or 0) != project_id:
            raise RuntimeError("runtime block project_id mismatch")
        block = progress_data.get("block") if isinstance(progress_data.get("block"), dict) else {}
        if str(progress_data.get("block_key") or "").strip() != "progress":
            raise RuntimeError("runtime block key mismatch")
        if str(block.get("block_type") or "").strip() != "progress_summary":
            raise RuntimeError("runtime progress block type mismatch")

        next_actions_hint = block_hints.get("next_actions") if isinstance(block_hints.get("next_actions"), dict) else {}
        status, next_actions_resp = _post(
            intent_url,
            token,
            str(next_actions_hint.get("intent") or "project.dashboard.block.fetch"),
            next_actions_hint.get("params") if isinstance(next_actions_hint.get("params"), dict) else {"project_id": project_id, "block_key": "next_actions"},
            db_name=db_name,
        )
        _assert_ok(status, next_actions_resp, "project.dashboard.block.fetch(next_actions)")
        next_actions_data = next_actions_resp.get("data") if isinstance(next_actions_resp.get("data"), dict) else {}
        next_block = next_actions_data.get("block") if isinstance(next_actions_data.get("block"), dict) else {}
        if str(next_actions_data.get("block_key") or "").strip() != "next_actions":
            raise RuntimeError("runtime next_actions block key mismatch")
        if str(next_block.get("block_type") or "").strip() != "action_list":
            raise RuntimeError("runtime next_actions block type mismatch")

        report["flow"] = {
            "project_id": project_id,
            "suggested_action_intent": suggested_intent,
            "dashboard_entry_keys": sorted(dash_entry.keys()),
            "runtime_block_key": str(progress_data.get("block_key") or ""),
            "runtime_block_state": str(block.get("state") or ""),
            "runtime_next_actions_state": str(next_block.get("state") or ""),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_dashboard_flow_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_dashboard_flow_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
