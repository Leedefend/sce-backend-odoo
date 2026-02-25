#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "multi_tenant_evolution_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "multi_tenant_evolution_report.json"


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[int, dict]:
    return http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )


def _intent(intent_url: str, token: str, intent: str, params: dict, headers: dict | None = None) -> tuple[int, dict]:
    h = {"Authorization": f"Bearer {token}"}
    if isinstance(headers, dict):
        h.update(headers)
    return http_post_json(intent_url, {"intent": intent, "params": params}, headers=h)


def _shape(data: dict) -> list[str]:
    if isinstance(data.get("data"), dict):
        data = data.get("data")
    if not isinstance(data, dict):
        return []
    return sorted(data.keys())


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_primary = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    db_alt = str(os.getenv("DB_NAME_ALT") or "sc_dev_alt").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    status_login, payload_login = _login(intent_url, db_primary, login, password)
    if status_login >= 400 or not isinstance(payload_login, dict) or payload_login.get("ok") is not True:
        errors.append("primary db login failed")
        token = ""
    else:
        token = str(((payload_login.get("data") or {}).get("token")) or "")
        if not token:
            errors.append("primary db token missing")

    primary_shape_before: list[str] = []
    primary_shape_after: list[str] = []
    alt_status = 0
    alt_ok = False
    if token:
        status_a, payload_a = _intent(
            intent_url,
            token,
            "system.init",
            {"contract_mode": "user", "db": db_primary},
            headers={"X-Odoo-DB": db_primary},
        )
        if status_a >= 400 or not isinstance(payload_a, dict) or payload_a.get("ok") is not True:
            errors.append("primary system.init failed before cross-tenant probe")
        else:
            primary_shape_before = _shape(payload_a.get("data") if isinstance(payload_a.get("data"), dict) else {})

        # probe cross-tenant db using same channel (expected fail if DB missing)
        alt_status, alt_payload = _intent(
            intent_url,
            token,
            "system.init",
            {"contract_mode": "user", "db": db_alt},
            headers={"X-Odoo-DB": db_alt},
        )
        alt_ok = alt_status < 400 and isinstance(alt_payload, dict) and alt_payload.get("ok") is True
        if alt_ok:
            warnings.append("alt db probe succeeded; ensure this is expected in multi-db environment")

        status_b, payload_b = _intent(
            intent_url,
            token,
            "system.init",
            {"contract_mode": "user", "db": db_primary},
            headers={"X-Odoo-DB": db_primary},
        )
        if status_b >= 400 or not isinstance(payload_b, dict) or payload_b.get("ok") is not True:
            errors.append("primary system.init failed after cross-tenant probe")
        else:
            primary_shape_after = _shape(payload_b.get("data") if isinstance(payload_b.get("data"), dict) else {})
            if primary_shape_before and primary_shape_after and primary_shape_before != primary_shape_after:
                errors.append("primary system.init shape changed after cross-tenant probe")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "db_primary": db_primary,
            "db_alt": db_alt,
            "alt_status": alt_status,
            "alt_ok": alt_ok,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "primary_shape_before": primary_shape_before,
        "primary_shape_after": primary_shape_after,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Multi-Tenant Evolution Report",
        "",
        f"- db_primary: {db_primary}",
        f"- db_alt: {db_alt}",
        f"- alt_status: {alt_status}",
        f"- alt_ok: {alt_ok}",
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
        print("[multi_tenant_evolution_smoke] FAIL")
        return 2
    print("[multi_tenant_evolution_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
