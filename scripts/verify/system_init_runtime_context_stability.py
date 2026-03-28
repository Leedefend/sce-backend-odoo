#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json

ART_DIR = Path("artifacts/backend")
JSON_OUT = ART_DIR / "system_init_runtime_context_stability.json"
MD_OUT = ART_DIR / "system_init_runtime_context_stability.md"


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, "login")
    data = (resp or {}).get("data") or {}
    token = data.get("token")
    if not token and isinstance(data.get("session"), dict):
        token = data.get("session", {}).get("token")
    if not token:
        raise RuntimeError("login missing token")
    return str(token)


def _request_system_init(intent_url: str, token: str, params: dict, label: str) -> dict:
    status, resp = http_post_json(
        intent_url,
        {"intent": "system.init", "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, label)
    return resp


def _bool(v) -> bool:
    return bool(v)


def _is_startup_contract_valid(data: dict, *, expected_mode: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    init_meta = data.get("init_meta") if isinstance(data.get("init_meta"), dict) else {}
    scene_ready = data.get("scene_ready_contract_v1") if isinstance(data.get("scene_ready_contract_v1"), dict) else {}
    scenes = scene_ready.get("scenes") if isinstance(scene_ready.get("scenes"), list) else []
    nav = data.get("nav") if isinstance(data.get("nav"), list) else []
    role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}

    if init_meta.get("contract_mode") != expected_mode:
        errors.append(f"init_meta.contract_mode expected {expected_mode}")
    if not isinstance(nav, list) or not nav:
        errors.append("nav missing or empty")
    if not isinstance(role_surface, dict) or not str(role_surface.get("role_code") or "").strip():
        errors.append("role_surface.role_code missing")
    if not isinstance(scene_ready, dict):
        errors.append("scene_ready_contract_v1 missing")
    if not isinstance(scenes, list) or not scenes:
        errors.append("scene_ready_contract_v1.scenes missing or empty")
    if bool(init_meta.get("preload_requested")):
        errors.append("init_meta.preload_requested must be false for boot probe")

    return (not errors), errors


def main() -> None:
    ART_DIR.mkdir(parents=True, exist_ok=True)

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = os.getenv("E2E_DB") or os.getenv("DB_NAME") or ""
    login = os.getenv("E2E_LOGIN") or "admin"
    password = os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin"
    token = _login(intent_url, db_name, login, password)

    checks = []
    errors: list[str] = []

    user_resp = _request_system_init(intent_url, token, {"contract_mode": "user"}, "system.init.user")
    user_data = (user_resp or {}).get("data") if isinstance((user_resp or {}).get("data"), dict) else {}
    user_ok, user_errors = _is_startup_contract_valid(user_data, expected_mode="user")
    checks.append({"label": "user_mode", "ok": _bool(user_ok)})
    if not user_ok:
        errors.append(f"user_mode: {'; '.join(user_errors)}")

    hud_resp = _request_system_init(intent_url, token, {"contract_mode": "hud"}, "system.init.hud")
    hud_data = (hud_resp or {}).get("data") if isinstance((hud_resp or {}).get("data"), dict) else {}
    hud_ok, hud_errors = _is_startup_contract_valid(hud_data, expected_mode="hud")
    checks.append({"label": "hud_mode", "ok": _bool(hud_ok)})
    if not hud_ok:
        errors.append(f"hud_mode: {'; '.join(hud_errors)}")

    injected_resp = _request_system_init(
        intent_url,
        token,
        {"contract_mode": "hud", "scene_inject_critical_error": 1},
        "system.init.hud.injected",
    )
    injected_data = (
        (injected_resp or {}).get("data") if isinstance((injected_resp or {}).get("data"), dict) else {}
    )
    injected_ok, injected_errors = _is_startup_contract_valid(injected_data, expected_mode="hud")
    checks.append(
        {
            "label": "hud_injected_critical",
            "ok": _bool(injected_ok),
        }
    )
    if not injected_ok:
        errors.append(f"hud_injected_critical: {'; '.join(injected_errors)}")

    result = {
        "ok": not errors,
        "db": db_name,
        "login": login,
        "checks": checks,
        "errors": errors,
    }
    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# System Init Runtime Context Stability",
        "",
        f"- ok: `{str(result['ok']).lower()}`",
        f"- db: `{db_name}`",
        f"- login: `{login}`",
        "",
        "## Checks",
    ]
    for row in checks:
        suffix = ""
        if "auto_degrade_triggered" in row:
            suffix = f" (auto_degrade_triggered={str(bool(row['auto_degrade_triggered'])).lower()})"
        lines.append(f"- {row['label']}: {'PASS' if row['ok'] else 'FAIL'}{suffix}")
    if errors:
        lines.append("")
        lines.append("## Errors")
        for err in errors:
            lines.append(f"- {err}")
    MD_OUT.write_text("\n".join(lines), encoding="utf-8")

    print(str(JSON_OUT.resolve()))
    print(str(MD_OUT.resolve()))
    if errors:
        raise RuntimeError("; ".join(errors))
    print("[system_init_runtime_context_stability] PASS")


if __name__ == "__main__":
    main()
