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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_execution_pilot_precheck_guard.json"


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


def _fetch_pilot_precheck(intent_url: str, token: str, db_name: str, project_id: int) -> dict:
    status, response = _post(
        intent_url,
        token,
        "project.execution.block.fetch",
        {"project_id": project_id, "block_key": "pilot_precheck"},
        db_name=db_name,
    )
    _assert_ok(status, response, "project.execution.block.fetch(pilot_precheck)")
    block = (((response.get("data") or {}).get("block")) or {})
    data = block.get("data") if isinstance(block.get("data"), dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    checks = data.get("checks") if isinstance(data.get("checks"), list) else []
    return {"block": block, "summary": summary, "checks": checks}


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
                "name": f"P15A-PRECHECK-{uuid4().hex[:8]}",
                "description": "pilot precheck guard",
                "date_start": str(os.getenv("P15A_DATE_START") or "2026-03-23"),
            },
            db_name=db_name,
        )
        _assert_ok(status, create_resp, "project.initiation.enter")
        project_id = int((((create_resp.get("data") or {}) if isinstance(create_resp.get("data"), dict) else {}).get("record") or {}).get("id") or 0)
        if project_id <= 0:
            raise RuntimeError("project id missing")

        precheck = _fetch_pilot_precheck(intent_url, token, db_name, project_id)
        if str((precheck.get("block") or {}).get("block_type") or "") != "checklist":
            raise RuntimeError(f"pilot_precheck block_type drift: {precheck.get('block')}")
        summary = precheck.get("summary") if isinstance(precheck.get("summary"), dict) else {}
        checks = precheck.get("checks") if isinstance(precheck.get("checks"), list) else []
        if str(summary.get("overall_state") or "") != "ready":
            raise RuntimeError(f"fresh pilot_precheck should be ready: {summary}")
        if int(summary.get("failed_count") or 0) != 0:
            raise RuntimeError(f"fresh pilot_precheck failed_count drift: {summary}")
        if str(summary.get("single_open_task_only") or "") not in {"True", "true"} and summary.get("single_open_task_only") is not True:
            raise RuntimeError(f"single_open_task_only flag missing: {summary}")
        required_checks = {
            "root_task",
            "single_open_task",
            "execution_task_consistency",
            "required_fields",
            "activity_rule",
            "lifecycle_state",
        }
        seen = {str((row or {}).get("key") or "") for row in checks if isinstance(row, dict)}
        if seen != required_checks:
            raise RuntimeError(f"pilot_precheck checks drift: {sorted(seen)}")
        if any(str((row or {}).get("status") or "") != "pass" for row in checks if isinstance(row, dict)):
            raise RuntimeError(f"fresh pilot_precheck should pass all checks: {checks}")

        report["pilot_precheck"] = {
            "project_id": project_id,
            "overall_state": str(summary.get("overall_state") or ""),
            "check_keys": sorted(seen),
            "failed_count": int(summary.get("failed_count") or 0),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_execution_pilot_precheck_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_execution_pilot_precheck_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
