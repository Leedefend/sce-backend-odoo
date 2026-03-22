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
OUT_JSON = ROOT / "artifacts" / "backend" / "portal_minimum_runtime_surface_guard.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def _collect_block_count(workspace_home: dict[str, Any], scene_ready_v1: dict[str, Any]) -> int:
    count = 0
    blocks = workspace_home.get("blocks") if isinstance(workspace_home.get("blocks"), list) else []
    count += len([row for row in blocks if isinstance(row, dict)])

    zones = scene_ready_v1.get("zones") if isinstance(scene_ready_v1.get("zones"), dict) else {}
    for zone in zones.values():
        if not isinstance(zone, dict):
            continue
        z_blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        count += len([row for row in z_blocks if isinstance(row, dict)])
    return count


def _contains_error_panel(workspace_home: dict[str, Any], scene_ready_v1: dict[str, Any]) -> bool:
    candidates: list[dict[str, Any]] = []
    blocks = workspace_home.get("blocks") if isinstance(workspace_home.get("blocks"), list) else []
    candidates.extend([row for row in blocks if isinstance(row, dict)])
    zones = scene_ready_v1.get("zones") if isinstance(scene_ready_v1.get("zones"), dict) else {}
    for zone in zones.values():
        if not isinstance(zone, dict):
            continue
        z_blocks = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        candidates.extend([row for row in z_blocks if isinstance(row, dict)])

    for block in candidates:
        key = str(block.get("key") or "").strip().lower()
        title = str(block.get("title") or "").strip().lower()
        if "error_panel" in key or key == "error" or "错误" in title or "error" in title:
            return True
    return False


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
    if status >= 400 or login_resp.get("ok") is not True:
        errors.append(f"login failed: status={status}")
    token = (((login_resp.get("data") or {}) if isinstance(login_resp.get("data"), dict) else {}).get("session") or {}).get("token")
    token = str(token or "").strip()
    if not token:
        errors.append("login token missing")

    if token:
        status, init_resp = _post(intent_url, token, "system.init", {"with_preload": False, "contract_mode": "default"}, db_name=db_name)
        if status >= 400 or init_resp.get("ok") is not True:
            errors.append(f"system.init(with_preload=false) failed: status={status}")
        init_data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}

        default_route = init_data.get("default_route") if isinstance(init_data.get("default_route"), dict) else {}
        route = str(default_route.get("route") or "").strip()
        if route.startswith("/workbench"):
            errors.append(f"default_route must not fallback to workbench: {route}")

        status, catalog_resp = _post(intent_url, token, "app.catalog", {}, db_name=db_name)
        if status >= 400 or catalog_resp.get("ok") is not True:
            errors.append(f"app.catalog failed: status={status}")
        catalog_data = catalog_resp.get("data") if isinstance(catalog_resp.get("data"), dict) else {}
        apps = catalog_data.get("apps") if isinstance(catalog_data.get("apps"), list) else []
        workspace_app = None
        for row in apps:
            if not isinstance(row, dict):
                continue
            app_id = str((row.get("meta") or {}).get("app_id") or "").strip() or str(row.get("key") or "").replace("app:", "", 1)
            if app_id == "workspace":
                workspace_app = row
                break
        if workspace_app is None:
            errors.append("app.catalog missing workspace app")

        status, open_resp = _post(intent_url, token, "app.open", {"app": "workspace"}, db_name=db_name)
        if status >= 400 or open_resp.get("ok") is not True:
            errors.append(f"app.open(workspace) failed: status={status}")
        open_data = open_resp.get("data") if isinstance(open_resp.get("data"), dict) else {}
        open_subject = str(open_data.get("subject") or "").strip()
        open_route = str(open_data.get("route") or "").strip()
        if open_subject != "ui.contract":
            errors.append(f"app.open(workspace) subject expected ui.contract, got {open_subject!r}")
        if open_route.startswith("/workbench"):
            errors.append(f"app.open(workspace) must not fallback to workbench: {open_route}")

        # same-route residency: calling app.open(workspace) repeatedly must remain successful.
        status, open_again_resp = _post(intent_url, token, "app.open", {"app": "workspace"}, db_name=db_name)
        if status >= 400 or open_again_resp.get("ok") is not True:
            errors.append(f"app.open(workspace) same-route replay failed: status={status}")

        # preload contract surface: must be non-empty and block-renderable.
        status, preload_resp = _post(intent_url, token, "system.init", {"with_preload": True, "contract_mode": "default"}, db_name=db_name)
        if status >= 400 or preload_resp.get("ok") is not True:
            errors.append(f"system.init(with_preload=true) failed: status={status}")
        preload_data = preload_resp.get("data") if isinstance(preload_resp.get("data"), dict) else {}
        workspace_home = preload_data.get("workspace_home") if isinstance(preload_data.get("workspace_home"), dict) else {}
        scene_ready_v1 = preload_data.get("scene_ready_contract_v1") if isinstance(preload_data.get("scene_ready_contract_v1"), dict) else {}
        block_count = _collect_block_count(workspace_home, scene_ready_v1)
        if block_count <= 0:
            errors.append("minimum runtime page is empty: no blocks rendered")
        if _contains_error_panel(workspace_home, scene_ready_v1):
            errors.append("error panel detected in minimum runtime surface")

        report["checks"].append(
            {
                "default_route": default_route,
                "app_open": {"subject": open_subject, "route": open_route},
                "workspace_home_loaded": bool(workspace_home),
                "scene_ready_loaded": bool(scene_ready_v1),
                "block_count": block_count,
            }
        )

    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    _write_json(OUT_JSON, report)

    if errors:
        print("[portal_minimum_runtime_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[portal_minimum_runtime_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _write_json(OUT_JSON, {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]})
        print("[portal_minimum_runtime_surface_guard] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)

