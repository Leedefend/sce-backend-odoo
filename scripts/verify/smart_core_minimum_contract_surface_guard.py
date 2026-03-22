#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "smart_core_minimum_contract_surface_guard.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_envelope(payload: dict[str, Any], intent: str, errors: list[str]) -> None:
    if not isinstance(payload, dict):
        errors.append(f"{intent}: payload is not object")
        return
    for key in ("ok", "data", "meta"):
        if key not in payload:
            errors.append(f"{intent}: missing envelope key `{key}`")
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    if not meta:
        errors.append(f"{intent}: meta is missing or invalid")
        return
    if not str(meta.get("intent") or "").strip():
        errors.append(f"{intent}: meta.intent missing")
    if not str(meta.get("trace_id") or "").strip():
        errors.append(f"{intent}: meta.trace_id missing")


def _post(
    intent_url: str,
    token: str | None,
    intent: str,
    params: dict[str, Any] | None = None,
    *,
    db_name: str = "",
) -> tuple[int, dict[str, Any]]:
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {"checks": []}
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
    _assert_envelope(login_resp, "login", errors)
    if status >= 400 or login_resp.get("ok") is not True:
        errors.append(f"login failed: status={status}")
    token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
    if not str(token or "").strip():
        errors.append("login: data.session.token missing")
        token = ""
    login_data = login_resp.get("data") if isinstance(login_resp.get("data"), dict) else {}
    for key in ("session", "user", "entitlement", "bootstrap", "contract"):
        if key not in login_data:
            errors.append(f"login: missing data.{key}")

    if token:
        status, init_resp = _post(intent_url, token, "system.init", {"contract_mode": "user"}, db_name=db_name)
        _assert_envelope(init_resp, "system.init", errors)
        if status >= 400 or init_resp.get("ok") is not True:
            errors.append(f"system.init failed: status={status}")
        init_data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        nav = init_data.get("nav")
        if not isinstance(nav, list):
            errors.append("system.init: data.nav must be list")
        if "default_route" not in init_data:
            errors.append("system.init: missing data.default_route")

        status, catalog_resp = _post(intent_url, token, "app.catalog", {}, db_name=db_name)
        _assert_envelope(catalog_resp, "app.catalog", errors)
        if status >= 400 or catalog_resp.get("ok") is not True:
            errors.append(f"app.catalog failed: status={status}")
        catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
        apps = catalog_data.get("apps") if isinstance(catalog_data.get("apps"), list) else []
        if not apps:
            errors.append("app.catalog: data.apps is empty")

        workspace_app = None
        for item in apps:
            if not isinstance(item, dict):
                continue
            app_id = str((item.get("meta") or {}).get("app_id") or "").strip() or str(item.get("key") or "").replace("app:", "", 1)
            if app_id == "workspace":
                workspace_app = item
                break
        if workspace_app is None:
            errors.append("minimum surface baseline broken: workspace app missing in app.catalog")

        app_param = "workspace"

        status, nav_resp = _post(intent_url, token, "app.nav", {"app": app_param}, db_name=db_name)
        _assert_envelope(nav_resp, "app.nav", errors)
        if status >= 400 or nav_resp.get("ok") is not True:
            errors.append(f"app.nav failed: status={status}")
        nav_data = nav_resp.get("data") if isinstance(nav_resp.get("data"), dict) else {}
        if not isinstance(nav_data.get("sections"), list):
            errors.append("app.nav: data.sections must be list")

        status, open_resp = _post(intent_url, token, "app.open", {"app": app_param}, db_name=db_name)
        _assert_envelope(open_resp, "app.open", errors)
        if status >= 400 or open_resp.get("ok") is not True:
            errors.append(f"app.open failed: status={status}")
        open_data = open_resp.get("data") if isinstance(open_resp.get("data"), dict) else {}
        if str(open_data.get("subject") or "") != "ui.contract":
            errors.append("app.open: data.subject must be ui.contract")
        if not str(open_data.get("scene_key") or "").strip():
            errors.append("app.open: data.scene_key missing")
        if not str(open_data.get("route") or "").strip():
            errors.append("app.open: data.route missing")

        status, meta_resp = _post(intent_url, token, "meta.describe_model", {"model": "res.users"}, db_name=db_name)
        _assert_envelope(meta_resp, "meta.describe_model", errors)
        if status >= 400 or meta_resp.get("ok") is not True:
            errors.append(f"meta.describe_model failed: status={status}")

        status, permission_resp = _post(intent_url, token, "permission.check", {"capability_key": "platform.home"}, db_name=db_name)
        _assert_envelope(permission_resp, "permission.check", errors)
        if status >= 400 or permission_resp.get("ok") is not True:
            errors.append(f"permission.check failed: status={status}")
        permission_data = permission_resp.get("data") if isinstance(permission_resp.get("data"), dict) else {}
        if "allow" not in permission_data:
            errors.append("permission.check: data.allow missing")

    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    _write_json(OUT_JSON, report)

    if errors:
        print("[smart_core_minimum_contract_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[smart_core_minimum_contract_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        _write_json(OUT_JSON, report)
        print("[smart_core_minimum_contract_surface_guard] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
