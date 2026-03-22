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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_suggested_action_shape_guard.json"


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


def _assert_suggested_action_shape(data: dict) -> dict:
    payload = data.get("suggested_action_payload") if isinstance(data.get("suggested_action_payload"), dict) else {}
    if not payload:
        raise RuntimeError("suggested_action_payload missing")
    intent = str(payload.get("intent") or "").strip()
    params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
    reason_code = str(payload.get("reason_code") or params.get("reason_code") or "").strip()
    if not intent:
        raise RuntimeError("suggested_action_payload.intent missing")
    if not params:
        raise RuntimeError("suggested_action_payload.params missing")
    if not reason_code:
        raise RuntimeError("suggested_action_payload.reason_code missing")
    return {"intent": intent, "params": params, "reason_code": reason_code}


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
                "name": f"P12C-SA-{uuid4().hex[:8]}",
                "description": "Phase 12-C suggested_action shape guard",
                "date_start": str(os.getenv("P12C_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        _assert_ok(status, enter_resp, "project.initiation.enter")
        data = enter_resp.get("data") if isinstance(enter_resp.get("data"), dict) else {}
        shape = _assert_suggested_action_shape(data)
        report["suggested_action_shape"] = {
            "intent": shape["intent"],
            "reason_code": shape["reason_code"],
            "has_project_id": bool(int(shape["params"].get("project_id") or 0) > 0),
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_suggested_action_shape_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_suggested_action_shape_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

