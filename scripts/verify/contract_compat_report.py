#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
RULE_DOC = ROOT / "docs" / "contract" / "versioning_rules.md"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "contract_compat_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "contract_compat_report.json"


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token


def _intent_call(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )


def _has_versioning_markers(text: str) -> bool:
    required = ("api_version", "contract_version", "additive", "compatibility")
    low = text.lower()
    return all(item.lower() in low for item in required)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    if not RULE_DOC.is_file():
        errors.append("missing contract versioning rules doc")
    else:
        text = RULE_DOC.read_text(encoding="utf-8")
        if not _has_versioning_markers(text):
            errors.append("versioning_rules.md missing required compatibility markers")

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for contract compatibility probe")
        token = ""

    system_resp: dict = {}
    system_status = 0
    ui_resp: dict = {}
    ui_status = 0
    if token:
        system_status, system_resp = _intent_call(intent_url, token, "system.init", {"contract_mode": "user"})
        ui_status, ui_resp = _intent_call(
            intent_url,
            token,
            "ui.contract",
            {"op": "model", "model": "project.project", "view_type": "form"},
        )

    for name, status, payload in (
        ("system.init", system_status, system_resp),
        ("ui.contract", ui_status, ui_resp),
    ):
        if status >= 400 or not isinstance(payload, dict):
            errors.append(f"{name} runtime response unavailable for compatibility check")
            continue
        for key in ("ok", "data", "meta"):
            if key not in payload:
                errors.append(f"{name} missing envelope key: {key}")
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if "trace_id" not in meta:
            warnings.append(f"{name} meta.trace_id missing")
        if name == "ui.contract":
            for key in ("schema_version", "api_version", "contract_version"):
                if key not in meta:
                    errors.append(f"{name} missing version key: {key}")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "system_status": system_status,
            "ui_contract_status": ui_status,
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Contract Compatibility Report",
        "",
        f"- system_status: {system_status}",
        f"- ui_contract_status: {ui_status}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "## Errors",
        "",
    ]
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[contract_compat_report] FAIL")
        return 2
    print("[contract_compat_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
