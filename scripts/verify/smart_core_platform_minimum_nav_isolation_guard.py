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
OUT_JSON = ROOT / "artifacts" / "backend" / "smart_core_platform_minimum_nav_isolation_guard.json"


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


def _collect_scene_keys(nodes: list[dict[str, Any]] | None) -> list[str]:
    out: list[str] = []

    def _walk(items: list[dict[str, Any]] | None) -> None:
        for item in items or []:
            if not isinstance(item, dict):
                continue
            scene_key = str(item.get("scene_key") or "").strip()
            if not scene_key:
                meta = item.get("meta") if isinstance(item.get("meta"), dict) else {}
                scene_key = str(meta.get("scene_key") or "").strip()
            if scene_key:
                out.append(scene_key)
            children = item.get("children") if isinstance(item.get("children"), list) else []
            _walk(children)

    _walk(nodes)
    return out


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
    if not str(token or "").strip():
        errors.append("login token missing")

    if token:
        status, init_resp = _post(intent_url, token, "system.init", {}, db_name=db_name)
        if status >= 400 or init_resp.get("ok") is not True:
            errors.append(f"system.init failed: status={status}")
        init_data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        nav_meta = init_data.get("nav_meta") if isinstance(init_data.get("nav_meta"), dict) else {}
        nav_source = str(nav_meta.get("nav_source") or "").strip()
        platform_minimum_surface = bool(nav_meta.get("platform_minimum_surface"))
        default_route = init_data.get("default_route") if isinstance(init_data.get("default_route"), dict) else {}
        scene_keys = _collect_scene_keys(init_data.get("nav") if isinstance(init_data.get("nav"), list) else [])

        report["checks"].append(
            {
                "nav_source": nav_source,
                "platform_minimum_surface": platform_minimum_surface,
                "default_route": default_route,
                "scene_keys": scene_keys,
            }
        )

        if not platform_minimum_surface:
            errors.append("system.init.nav_meta.platform_minimum_surface is not true")
        if nav_source != "platform_minimum_surface":
            errors.append(f"system.init.nav_meta.nav_source expected platform_minimum_surface, got {nav_source!r}")

        default_scene = str(default_route.get("scene_key") or "").strip()
        default_reason = str(default_route.get("reason") or "").strip()
        if default_scene != "workspace.home":
            errors.append(f"default_route.scene_key expected workspace.home, got {default_scene!r}")
        if default_reason != "platform_minimum_surface":
            errors.append(f"default_route.reason expected platform_minimum_surface, got {default_reason!r}")

        invalid_scene_keys = [key for key in scene_keys if key != "workspace.home"]
        if invalid_scene_keys:
            errors.append(
                "platform minimum nav contains non-workspace scenes: " + ", ".join(sorted(set(invalid_scene_keys)))
            )
        if not scene_keys:
            errors.append("platform minimum nav is empty")

    report["status"] = "PASS" if not errors else "FAIL"
    report["errors"] = errors
    _write_json(OUT_JSON, report)

    if errors:
        print("[smart_core_platform_minimum_nav_isolation_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[smart_core_platform_minimum_nav_isolation_guard] PASS")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        _write_json(OUT_JSON, report)
        print("[smart_core_platform_minimum_nav_isolation_guard] FAIL")
        print(f" - ENV_UNSTABLE: {exc}")
        sys.exit(1)
