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
    token = ((resp or {}).get("data") or {}).get("token")
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
    user_ok = (
        user_data.get("contract_mode") == "user"
        and isinstance(user_data.get("nav"), list)
        and not isinstance(user_data.get("hud"), dict)
    )
    checks.append({"label": "user_mode", "ok": _bool(user_ok)})
    if not user_ok:
        errors.append("user_mode: contract_mode/nav/hud expectation failed")

    hud_resp = _request_system_init(intent_url, token, {"contract_mode": "hud"}, "system.init.hud")
    hud_data = (hud_resp or {}).get("data") if isinstance((hud_resp or {}).get("data"), dict) else {}
    hud_diag = hud_data.get("scene_diagnostics") if isinstance(hud_data.get("scene_diagnostics"), dict) else {}
    hud_ok = (
        hud_data.get("contract_mode") == "hud"
        and isinstance(hud_data.get("hud"), dict)
        and isinstance(hud_diag, dict)
        and isinstance(hud_diag.get("auto_degrade"), dict)
    )
    checks.append({"label": "hud_mode", "ok": _bool(hud_ok)})
    if not hud_ok:
        errors.append("hud_mode: contract_mode/hud/scene_diagnostics expectation failed")

    injected_resp = _request_system_init(
        intent_url,
        token,
        {"contract_mode": "hud", "scene_inject_critical_error": 1},
        "system.init.hud.injected",
    )
    injected_data = (
        (injected_resp or {}).get("data") if isinstance((injected_resp or {}).get("data"), dict) else {}
    )
    injected_diag = (
        injected_data.get("scene_diagnostics") if isinstance(injected_data.get("scene_diagnostics"), dict) else {}
    )
    resolve_errors = injected_diag.get("resolve_errors") if isinstance(injected_diag.get("resolve_errors"), list) else []
    has_injected_error = any(
        isinstance(item, dict) and str(item.get("code") or "").strip() == "TEST_CRITICAL_INJECTED"
        for item in resolve_errors
    )
    auto_degrade = injected_diag.get("auto_degrade") if isinstance(injected_diag.get("auto_degrade"), dict) else {}
    triggered = _bool(auto_degrade.get("triggered"))
    triggered_semantics_ok = True
    if triggered:
        action_taken = str(auto_degrade.get("action_taken") or "").strip()
        if not action_taken:
            triggered_semantics_ok = False
        if action_taken == "rollback_pinned":
            if str(injected_data.get("scene_channel") or "") != "stable":
                triggered_semantics_ok = False
    injected_ok = isinstance(auto_degrade, dict) and (
        (triggered and triggered_semantics_ok) or (not triggered and has_injected_error)
    )
    checks.append(
        {
            "label": "hud_injected_critical",
            "ok": _bool(injected_ok),
            "auto_degrade_triggered": triggered,
        }
    )
    if not injected_ok:
        errors.append("hud_injected_critical: injected error or auto_degrade semantics invalid")

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
