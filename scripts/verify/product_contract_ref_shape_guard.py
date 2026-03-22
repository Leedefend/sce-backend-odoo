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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_contract_ref_shape_guard.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _is_menu_contract(params: dict) -> bool:
    op = str(params.get("op") or "").strip().lower()
    if op != "menu":
        return False
    menu_id = int(params.get("menu_id") or 0)
    menu_xmlid = str(params.get("menu_xmlid") or "").strip()
    return menu_id > 0 or bool(menu_xmlid)


def _is_model_contract(params: dict) -> bool:
    op = str(params.get("op") or "").strip().lower()
    model = str(params.get("model") or "").strip()
    return op == "model" and bool(model)


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS"}
    errors: list[str] = []

    try:
        status, login_resp = _post(
            intent_url,
            None,
            "login",
            {"db": db_name, "login": login, "password": password},
            db_name=db_name,
        )
        if status >= 400 or login_resp.get("ok") is not True:
            raise RuntimeError(f"login failed status={status}")
        token = ((((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token"))
        token = str(token or "").strip()
        if not token:
            raise RuntimeError("login token missing")

        status, create_resp = _post(
            intent_url,
            token,
            "project.initiation.enter",
            {
                "name": f"P12B-SHAPE-{uuid4().hex[:8]}",
                "description": "Phase 12-B contract_ref shape guard",
                "date_start": str(os.getenv("P12B_DATE_START") or "2026-03-22"),
            },
            db_name=db_name,
        )
        if status >= 400 or create_resp.get("ok") is not True:
            raise RuntimeError(f"project.initiation.enter failed status={status} payload={create_resp}")

        data = create_resp.get("data") if isinstance(create_resp.get("data"), dict) else {}
        contract_ref = data.get("contract_ref") if isinstance(data.get("contract_ref"), dict) else {}
        suggested_payload = data.get("suggested_action_payload") if isinstance(data.get("suggested_action_payload"), dict) else {}

        ref_intent = str(contract_ref.get("intent") or "").strip()
        if ref_intent != "ui.contract":
            errors.append(f"contract_ref.intent expected ui.contract, got {ref_intent!r}")

        ref_params = contract_ref.get("params") if isinstance(contract_ref.get("params"), dict) else {}
        if not ref_params:
            errors.append("contract_ref.params missing")

        menu_primary = _is_menu_contract(ref_params)
        model_fallback = _is_model_contract(ref_params)
        if not menu_primary and not model_fallback:
            errors.append(
                "contract_ref params invalid: expected primary op=menu(menu_id/menu_xmlid) or fallback op=model(model)"
            )

        report["contract_ref"] = contract_ref
        report["suggested_action_payload"] = suggested_payload
        report["shape"] = {
            "menu_primary": menu_primary,
            "model_fallback": model_fallback,
        }
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        print("[product_contract_ref_shape_guard] FAIL")
        print(f" - {exc}")
        return 1

    if errors:
        report["status"] = "FAIL"
        report["errors"] = errors
        _write_json(OUT_JSON, report)
        print("[product_contract_ref_shape_guard] FAIL")
        for error in errors:
            print(f" - {error}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_contract_ref_shape_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
