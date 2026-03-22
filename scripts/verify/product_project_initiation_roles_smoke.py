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
OUT_JSON = ROOT / "artifacts" / "backend" / "product_project_initiation_roles_smoke.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _role_defs() -> list[dict]:
    return [
        {
            "role": "owner",
            "login": str(os.getenv("ROLE_OWNER_LOGIN") or "demo_role_owner").strip(),
            "password": str(os.getenv("ROLE_OWNER_PASSWORD") or "demo").strip(),
            "expect_create": False,
        },
        {
            "role": "pm",
            "login": str(os.getenv("ROLE_PM_LOGIN") or "demo_role_pm").strip(),
            "password": str(os.getenv("ROLE_PM_PASSWORD") or "demo").strip(),
            "expect_create": True,
        },
        {
            "role": "finance",
            "login": str(os.getenv("ROLE_FINANCE_LOGIN") or "demo_role_finance").strip(),
            "password": str(os.getenv("ROLE_FINANCE_PASSWORD") or "demo").strip(),
            "expect_create": False,
        },
        {
            "role": "executive",
            "login": str(os.getenv("ROLE_EXECUTIVE_LOGIN") or "demo_role_executive").strip(),
            "password": str(os.getenv("ROLE_EXECUTIVE_PASSWORD") or "demo").strip(),
            "expect_create": True,
        },
    ]


def _expect_contract_safe(payload: dict, *, label: str) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label}: invalid payload")
    if payload.get("ok") is True:
        return
    error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
    code = str(error.get("code") or "").strip()
    if not code:
        raise RuntimeError(f"{label}: non-ok response missing error.code")


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report = {"status": "PASS", "db": db_name, "roles": []}
    errors: list[str] = []

    for role in _role_defs():
        role_name = str(role.get("role") or "").strip()
        login = str(role.get("login") or "").strip()
        password = str(role.get("password") or "").strip()
        expect_create = bool(role.get("expect_create"))
        role_result: dict = {"role": role_name, "login": login, "expect_create": expect_create}

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

            status, init_resp = _post(
                intent_url,
                token,
                "system.init",
                {"with_preload": True, "contract_mode": "default"},
                db_name=db_name,
            )
            if status >= 400 or init_resp.get("ok") is not True:
                raise RuntimeError(f"system.init failed status={status}")

            status, open_resp = _post(
                intent_url,
                token,
                "app.open",
                {"app": "project_management", "feature": "project_initiation"},
                db_name=db_name,
            )
            if status >= 500:
                raise RuntimeError(f"app.open 500 status={status}")
            _expect_contract_safe(open_resp, label=f"{role_name}.app.open")
            open_data = open_resp.get("data") if isinstance(open_resp.get("data"), dict) else {}
            role_result["open_subject"] = str(open_data.get("subject") or "")
            role_result["open_scene_key"] = str(open_data.get("scene_key") or "")

            create_params = {
                "name": f"P12B-ROLE-{role_name}-{uuid4().hex[:8]}",
                "description": "Phase 12-B roles smoke",
                "date_start": str(os.getenv("P12B_DATE_START") or "2026-03-22"),
            }
            status, create_resp = _post(intent_url, token, "project.initiation.enter", create_params, db_name=db_name)
            if status >= 500:
                raise RuntimeError(f"project.initiation.enter 500 status={status}")
            _expect_contract_safe(create_resp, label=f"{role_name}.project.initiation.enter")

            create_ok = bool(create_resp.get("ok") is True)
            role_result["create_ok"] = create_ok
            role_result["create_error_code"] = str(
                ((create_resp.get("error") or {}) if isinstance(create_resp.get("error"), dict) else {}).get("code") or ""
            )

            if expect_create and not create_ok:
                raise RuntimeError(
                    f"expected create allow but got deny code={role_result['create_error_code'] or 'unknown'}"
                )
            if (not expect_create) and create_ok:
                raise RuntimeError("expected create deny but got allow")

            if create_ok:
                create_data = create_resp.get("data") if isinstance(create_resp.get("data"), dict) else {}
                suggested_action = str(create_data.get("suggested_action") or "").strip()
                if not suggested_action:
                    raise RuntimeError("create_ok but suggested_action missing")
                if suggested_action in {"open_workbench", "open_landing", "fallback"}:
                    raise RuntimeError(f"create_ok but suggested_action fallback leaked: {suggested_action}")
                role_result["suggested_action"] = suggested_action
            else:
                error = create_resp.get("error") if isinstance(create_resp.get("error"), dict) else {}
                deny_suggested = str(error.get("suggested_action") or "").strip()
                role_result["deny_suggested_action"] = deny_suggested

        except Exception as exc:
            errors.append(f"{role_name}: {exc}")
            role_result["status"] = "FAIL"
            role_result["error"] = str(exc)
        else:
            role_result["status"] = "PASS"

        report["roles"].append(role_result)

    if errors:
        report["status"] = "FAIL"
        report["errors"] = errors
        _write_json(OUT_JSON, report)
        print("[product_project_initiation_roles_smoke] FAIL")
        for err in errors:
            print(f" - {err}")
        return 1

    _write_json(OUT_JSON, report)
    print("[product_project_initiation_roles_smoke] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

