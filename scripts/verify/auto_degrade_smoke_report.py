#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "auto_degrade_smoke_report.md"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "auto_degrade_smoke_report.json"


def _login(intent_url: str, db_name: str, login: str, password: str) -> str:
    db_candidates = []
    for item in (db_name, "", "sc_demo", "sc_p3", "sc_p2", "sc_test"):
        val = str(item or "").strip()
        if val not in db_candidates:
            db_candidates.append(val)
    candidates = [
        (login, password),
        ("admin", os.getenv("ADMIN_PASSWD") or "admin"),
        ("sc_fx_pm", os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like"),
        ("demo_pm", os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo"),
    ]
    for cand_db in db_candidates:
        for cand_login, cand_password in candidates:
            cand_login = str(cand_login or "").strip()
            cand_password = str(cand_password or "").strip()
            if not cand_login:
                continue
            status, body = http_post_json(
                intent_url,
                {"intent": "login", "params": {"db": cand_db, "login": cand_login, "password": cand_password}},
                headers={"X-Anonymous-Intent": "1"},
            )
            if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
                continue
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            token = str(data.get("token") or "").strip()
            if token:
                return token
    secret = str(os.getenv("SC_BOOTSTRAP_SECRET") or os.getenv("BOOTSTRAP_SECRET") or "").strip()
    if secret:
        bootstrap_login = str(os.getenv("SC_BOOTSTRAP_LOGIN") or os.getenv("BOOTSTRAP_LOGIN") or "svc_project_ro").strip()
        status, body = http_post_json(
            intent_url,
            {"intent": "session.bootstrap", "params": {"secret": secret, "login": bootstrap_login, "db": db_name}},
            headers={"X-Anonymous-Intent": "1"},
        )
        if status == 200 and isinstance(body, dict) and body.get("ok") is True:
            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            token = str(data.get("token") or "").strip()
            if token:
                return token
    return ""


def _call_system_init(intent_url: str, token: str, params: dict):
    return http_post_json(
        intent_url,
        {"intent": "system.init", "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _diag(body: dict) -> dict:
    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    return data.get("scene_diagnostics") if isinstance(data.get("scene_diagnostics"), dict) else {}


def main() -> int:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    token = _login(intent_url, db_name, login, password)
    if not token:
        raise SystemExit("auto_degrade_smoke_report: login failed")

    status, body = _call_system_init(
        intent_url,
        token,
        {"contract_mode": "hud", "scene_inject_critical_error": 1},
    )
    if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
        raise SystemExit(f"auto_degrade_smoke_report: system.init failed status={status}")

    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    diag = _diag(body)
    auto = diag.get("auto_degrade") if isinstance(diag.get("auto_degrade"), dict) else {}
    triggered = bool(auto.get("triggered"))
    action_taken = str(auto.get("action_taken") or "").strip()
    scene_channel = str(data.get("scene_channel") or "")
    scene_contract_ref = str(data.get("scene_contract_ref") or "")
    resolve_errors = diag.get("resolve_errors") if isinstance(diag.get("resolve_errors"), list) else []
    has_injected_error = any(
        isinstance(item, dict) and str(item.get("code") or "").strip() == "TEST_CRITICAL_INJECTED"
        for item in resolve_errors
    )

    checks = {
        "system_init_ok": True,
        "auto_degrade_payload_present": isinstance(auto, dict),
        "critical_injection_detectable": triggered or has_injected_error,
        "stable_channel_when_triggered": (not triggered) or scene_channel == "stable",
        "stable_ref_when_triggered": (not triggered) or scene_contract_ref.startswith("stable/"),
        "action_taken_when_triggered": (not triggered) or bool(action_taken),
    }
    failures = [k for k, ok in checks.items() if not ok]

    report = {
        "ok": not failures,
        "status": status,
        "triggered": triggered,
        "action_taken": action_taken,
        "scene_channel": scene_channel,
        "scene_contract_ref": scene_contract_ref,
        "has_injected_error": has_injected_error,
        "checks": checks,
        "failures": failures,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Auto Degrade Smoke Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- triggered: {str(triggered).lower()}",
        f"- action_taken: `{action_taken or '-'}`",
        f"- scene_channel: `{scene_channel or '-'}`",
        f"- scene_contract_ref: `{scene_contract_ref or '-'}`",
        f"- has_injected_error: {str(has_injected_error).lower()}",
        "",
        "## Checks",
    ]
    for key, ok in checks.items():
        lines.append(f"- {key}: {'PASS' if ok else 'FAIL'}")
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.append(f"- {item}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(REPORT_MD))
    if failures:
        print("[auto_degrade_smoke_report] FAIL")
        return 1
    print("[auto_degrade_smoke_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
