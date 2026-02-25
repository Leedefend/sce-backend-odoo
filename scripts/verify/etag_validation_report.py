#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "etag_validation_report.md"
ARTIFACT_JSON = ROOT / "artifacts" / "backend" / "etag_validation_report.json"


def _extract_status_payload(resp):
    if isinstance(resp, tuple) and len(resp) == 2:
        return int(resp[0]), resp[1] if isinstance(resp[1], dict) else {}
    return 500, {}


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[str, str]:
    candidates = [
        (login, password),
        ("admin", os.getenv("ADMIN_PASSWD") or "admin"),
        ("sc_fx_pm", os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like"),
        ("demo_pm", os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo"),
    ]
    db_candidates = []
    for item in (db_name, "", "sc_demo", "sc_p3", "sc_p2", "sc_test"):
        val = str(item or "").strip()
        if val not in db_candidates:
            db_candidates.append(val)
    tried = []
    for cand_db in db_candidates:
        for cand_login, cand_password in candidates:
            cand_login = str(cand_login or "").strip()
            cand_password = str(cand_password or "").strip()
            if not cand_login:
                continue
            tried.append(f"{cand_login}@{cand_db or '<auto>'}")
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
                return token, cand_login
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
                return token, f"bootstrap:{bootstrap_login}"
    return "", ",".join(tried)


def _call(intent_url: str, token: str, intent: str, params: dict, etag: str = ""):
    headers = {"Authorization": f"Bearer {token}"}
    if etag:
        headers["If-None-Match"] = f'"{etag}"'
    return http_post_json(intent_url, {"intent": intent, "params": params}, headers=headers)


def _etag_of(body: dict) -> str:
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}
    return str(meta.get("etag") or "").strip()


def _scenario(intent_url: str, token: str, *, intent: str, p1: dict, p2: dict, require_304: bool) -> dict:
    s1, b1 = _call(intent_url, token, intent, p1)
    etag1 = _etag_of(b1 if isinstance(b1, dict) else {})
    s304, b304 = _call(intent_url, token, intent, p1, etag=etag1)
    s2, b2 = _call(intent_url, token, intent, p2)
    etag2 = _etag_of(b2 if isinstance(b2, dict) else {})
    return {
        "intent": intent,
        "require_304": bool(require_304),
        "p1": p1,
        "p2": p2,
        "first_status": int(s1),
        "first_has_etag": bool(etag1),
        "conditional_status": int(s304),
        "variation_status": int(s2),
        "etag_changed": bool(etag1 and etag2 and etag1 != etag2),
        "etag1": etag1,
        "etag2": etag2,
        "conditional_body_code": b304.get("code") if isinstance(b304, dict) else None,
    }


def main() -> int:
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    token, login_used = _login(intent_url, db_name, login, password)
    if not token:
        raise SystemExit(f"etag_validation_report: login failed (tried={login_used})")

    rows = [
        _scenario(
            intent_url,
            token,
            intent="system.init",
            p1={"contract_mode": "user"},
            p2={"contract_mode": "hud"},
            require_304=False,
        ),
        _scenario(
            intent_url,
            token,
            intent="ui.contract",
            p1={"op": "model", "model": "project.project", "view_type": "tree"},
            p2={"op": "model", "model": "res.partner", "view_type": "tree"},
            require_304=True,
        ),
        _scenario(
            intent_url,
            token,
            intent="api.data",
            p1={"op": "read", "model": "res.partner", "ids": [1], "fields": ["id", "name"]},
            p2={"op": "read", "model": "res.partner", "ids": [1], "fields": ["id", "display_name"]},
            require_304=True,
        ),
        _scenario(
            intent_url,
            token,
            intent="meta.describe_model",
            p1={"model": "res.partner"},
            p2={"model": "project.project"},
            require_304=True,
        ),
    ]

    failures = []
    for row in rows:
        if row["first_status"] != 200:
            failures.append(f"{row['intent']}: first_status={row['first_status']}")
        if not row["first_has_etag"]:
            failures.append(f"{row['intent']}: missing etag")
        if row["require_304"] and row["conditional_status"] != 304:
            failures.append(f"{row['intent']}: if-none-match not returning 304 ({row['conditional_status']})")
        if not row["etag_changed"]:
            failures.append(f"{row['intent']}: etag not changed on content variation")

    report = {
        "ok": not failures,
        "rows": rows,
        "failures": failures,
    }
    ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# ETag Validation Report",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- checks: {len(rows)}",
        f"- failures: {len(failures)}",
        "",
        "| intent | first_status | has_etag | conditional_status | etag_changed |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['intent']} | {row['first_status']} | "
            f"{'Y' if row['first_has_etag'] else 'N'} | {row['conditional_status']} | "
            f"{'Y' if row['etag_changed'] else 'N'} |"
        )
    if failures:
        lines.extend(["", "## Failures", ""])
        for item in failures:
            lines.append(f"- {item}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(ARTIFACT_JSON))
    print(str(REPORT_MD))
    if failures:
        print("[etag_validation_report] FAIL")
        return 1
    print("[etag_validation_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
