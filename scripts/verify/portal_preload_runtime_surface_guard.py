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
OUT_JSON = ROOT / "artifacts" / "backend" / "portal_preload_runtime_surface_guard.json"


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
        status, boot_resp = _post(intent_url, token, "system.init", {"with_preload": False, "contract_mode": "default"}, db_name=db_name)
        if status >= 400 or boot_resp.get("ok") is not True:
            errors.append(f"system.init(with_preload=false) failed: status={status}")
        boot_data = boot_resp.get("data") if isinstance(boot_resp.get("data"), dict) else {}

        status, preload_resp = _post(intent_url, token, "system.init", {"with_preload": True, "contract_mode": "default"}, db_name=db_name)
        if status >= 400 or preload_resp.get("ok") is not True:
            errors.append(f"system.init(with_preload=true) failed: status={status}")
        preload_data = preload_resp.get("data") if isinstance(preload_resp.get("data"), dict) else {}

        boot_forbidden = [
            key for key in ("workspace_home", "scene_ready_contract_v1", "page_contracts", "runtime_collections", "workspace_collections")
            if key in boot_data
        ]
        preload_forbidden = [
            key for key in ("page_contracts", "runtime_collections", "workspace_collections")
            if key in preload_data
        ]
        if boot_forbidden:
            errors.append("boot surface leaked preload/runtime keys: " + ", ".join(boot_forbidden))
        if preload_forbidden:
            errors.append("preload surface leaked runtime keys: " + ", ".join(preload_forbidden))

        workspace_home = preload_data.get("workspace_home") if isinstance(preload_data.get("workspace_home"), dict) else {}
        scene_ready_v1 = preload_data.get("scene_ready_contract_v1") if isinstance(preload_data.get("scene_ready_contract_v1"), dict) else {}
        if not workspace_home:
            errors.append("preload surface missing workspace_home")
        if not scene_ready_v1:
            errors.append("preload surface missing scene_ready_contract_v1")
        block_count = _collect_block_count(workspace_home, scene_ready_v1)
        if block_count <= 0:
            errors.append("preload surface is not renderable: no blocks found")

        init_meta = preload_data.get("init_meta") if isinstance(preload_data.get("init_meta"), dict) else {}
        if not bool(init_meta.get("preload_requested")):
            errors.append("preload surface init_meta.preload_requested must be true")

        report["checks"].append(
            {
                "boot_keys": sorted(boot_data.keys()),
                "preload_keys": sorted(preload_data.keys()),
                "boot_forbidden": boot_forbidden,
                "preload_forbidden": preload_forbidden,
                "workspace_home_loaded": bool(workspace_home),
                "scene_ready_loaded": bool(scene_ready_v1),
                "block_count": block_count,
            }
        )

    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    _write_json(OUT_JSON, report)

    if errors:
        print("[portal_preload_runtime_surface_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[portal_preload_runtime_surface_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        _write_json(OUT_JSON, {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]})
        print("[portal_preload_runtime_surface_guard] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
