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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_initiation_smoke.json"


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

    report = {"status": "PASS", "checks": []}

    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
        token = str(token or "").strip()
        if not token:
            raise RuntimeError("login response missing token")

        status, init_resp = _post(intent_url, token, "system.init", {"with_preload": True, "contract_mode": "default"}, db_name=db_name)
        _assert_ok(status, init_resp, "system.init")
        init_data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        default_route = init_data.get("default_route") if isinstance(init_data.get("default_route"), dict) else {}
        default_route_route = str(default_route.get("route") or "").strip()
        default_route_is_workbench = default_route_route.startswith("/workbench")

        # 打开产品场景：project.initiation（Phase-12A baseline）
        status, open_resp = _post(intent_url, token, "app.open", {"app": "project_management", "feature": "project_initiation"}, db_name=db_name)
        if status >= 400 or open_resp.get("ok") is not True:
            # 兼容旧 feature key，允许回退到 app-only openable-first
            status, open_resp = _post(intent_url, token, "app.open", {"app": "project_management"}, db_name=db_name)
        _assert_ok(status, open_resp, "app.open(project_management)")

        unique_name = f"P12A-INIT-{uuid4().hex[:8]}"
        create_params = {
            "name": unique_name,
            "description": "Phase 12-A product initiation smoke",
            "date_start": str(os.getenv("P12A_DATE_START") or "2026-03-22"),
        }
        status, enter_resp = _post(intent_url, token, "project.initiation.enter", create_params, db_name=db_name)
        _assert_ok(status, enter_resp, "project.initiation.enter")
        enter_data = enter_resp.get("data") if isinstance(enter_resp.get("data"), dict) else {}

        state = str(enter_data.get("state") or "").strip().lower()
        if state not in {"ready", "success"}:
            raise RuntimeError(f"project.initiation.enter state expected ready/success, got {state!r}")

        record = enter_data.get("record") if isinstance(enter_data.get("record"), dict) else {}
        record_id = int(record.get("id") or 0)
        if record_id <= 0:
            raise RuntimeError("project.initiation.enter missing created record id")

        suggested_action = str(enter_data.get("suggested_action") or "").strip()
        if not suggested_action:
            raise RuntimeError("project.initiation.enter missing suggested_action")
        if suggested_action in {"open_workbench", "open_landing", "fallback"}:
            raise RuntimeError(f"project.initiation.enter suggested_action fallback leaked: {suggested_action}")

        contract_ref = enter_data.get("contract_ref") if isinstance(enter_data.get("contract_ref"), dict) else {}
        contract_intent = str(contract_ref.get("intent") or "").strip() or "load_contract"
        contract_params = contract_ref.get("params") if isinstance(contract_ref.get("params"), dict) else {}
        if not contract_params:
            contract_params = {
                "model": "project.project",
                "res_id": record_id,
                "view_type": "form",
            }

        status, contract_resp = _post(intent_url, token, contract_intent, contract_params, db_name=db_name)
        contract_ok = status < 400 and contract_resp.get("ok") is True and isinstance(contract_resp.get("data"), dict) and bool(contract_resp.get("data"))

        if not contract_ok:
            suggested_payload = (
                enter_data.get("suggested_action_payload")
                if isinstance(enter_data.get("suggested_action_payload"), dict)
                else {}
            )
            fallback_intent = str(suggested_payload.get("intent") or "").strip()
            fallback_params = suggested_payload.get("params") if isinstance(suggested_payload.get("params"), dict) else {}
            if fallback_intent and fallback_params:
                status, contract_resp = _post(intent_url, token, fallback_intent, fallback_params, db_name=db_name)
                contract_ok = (
                    status < 400
                    and contract_resp.get("ok") is True
                    and isinstance(contract_resp.get("data"), dict)
                    and bool(contract_resp.get("data"))
                )
                if contract_ok:
                    contract_intent = fallback_intent

        if not contract_ok:
            raise RuntimeError(f"project initiation contract return failed: status={status} payload={contract_resp}")

        report["checks"].append(
            {
                "default_route": default_route,
                "default_route_is_workbench": default_route_is_workbench,
                "created_record_id": record_id,
                "suggested_action": suggested_action,
                "contract_intent": contract_intent,
            }
        )
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_project_initiation_smoke] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_initiation_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
