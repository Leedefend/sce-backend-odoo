#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "scene_drift_smoke_report.md"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "scene_drift_smoke_report.json"


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


def main() -> int:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    token = _login(intent_url, db_name, login, password)
    if not token:
        raise SystemExit("scene_drift_smoke_report: login failed")

    status, body = http_post_json(
        intent_url,
        {"intent": "system.init", "params": {"contract_mode": "hud"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
        raise SystemExit(f"scene_drift_smoke_report: system.init failed status={status}")

    data = body.get("data") if isinstance(body.get("data"), dict) else {}
    diag = data.get("scene_diagnostics") if isinstance(data.get("scene_diagnostics"), dict) else {}
    drift = diag.get("drift") if isinstance(diag.get("drift"), list) else []
    resolve_errors = diag.get("resolve_errors") if isinstance(diag.get("resolve_errors"), list) else []
    timings = diag.get("timings") if isinstance(diag.get("timings"), dict) else {}

    checks = {
        "scene_diagnostics_present": isinstance(diag, dict),
        "drift_list_present": isinstance(drift, list),
        "resolve_errors_list_present": isinstance(resolve_errors, list),
        "timings_resolve_ms_present": "resolve_ms" in timings,
        "timings_normalize_ms_present": "normalize_ms" in timings,
    }
    failures = [key for key, ok in checks.items() if not ok]

    report = {
        "ok": not failures,
        "drift_count": len(drift),
        "resolve_error_count": len(resolve_errors),
        "checks": checks,
        "failures": failures,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Scene Drift Smoke Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- drift_count: {report['drift_count']}",
        f"- resolve_error_count: {report['resolve_error_count']}",
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
        print("[scene_drift_smoke_report] FAIL")
        return 1
    print("[scene_drift_smoke_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
