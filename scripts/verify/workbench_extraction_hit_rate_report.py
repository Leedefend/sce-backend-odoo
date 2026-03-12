#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from intent_smoke_utils import require_ok
from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "workbench_extraction_hit_rate_report.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "workbench_extraction_hit_rate_report.md"


def _to_text(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _resolve_roles() -> list[dict[str, Any]]:
    default_prod_like = _to_text(os.getenv("E2E_PROD_LIKE_PASSWORD") or "prod_like")
    default_demo = _to_text(os.getenv("E2E_ROLE_MATRIX_DEFAULT_PASSWORD") or "demo")
    return [
        {
            "role": "pm",
            "login": _to_text(os.getenv("ROLE_PM_LOGIN") or "sc_fx_pm"),
            "password_candidates": [
                _to_text(os.getenv("ROLE_PM_PASSWORD")),
                default_prod_like,
                default_demo,
            ],
        },
        {
            "role": "finance",
            "login": _to_text(os.getenv("ROLE_FINANCE_LOGIN") or "sc_fx_finance"),
            "password_candidates": [
                _to_text(os.getenv("ROLE_FINANCE_PASSWORD")),
                default_prod_like,
                default_demo,
            ],
        },
        {
            "role": "owner",
            "login": _to_text(os.getenv("ROLE_OWNER_LOGIN") or "sc_fx_executive"),
            "password_candidates": [
                _to_text(os.getenv("ROLE_OWNER_PASSWORD")),
                default_prod_like,
                default_demo,
            ],
        },
    ]


def _login(intent_url: str, db_name: str, login: str, password_candidates: list[str]) -> str:
    failures: list[str] = []
    for password in [item for item in password_candidates if _to_text(item)]:
        status, resp = http_post_json(
            intent_url,
            {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
            headers={"X-Anonymous-Intent": "1"},
        )
        if status == 200 and bool(resp.get("ok")):
            data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
            token = _to_text(data.get("token"))
            if token:
                return token
            failures.append(f"password={password}: missing token")
            continue
        failures.append(f"password={password}: status={status}")
    raise RuntimeError(f"login({login}) failed with candidates; {'; '.join(failures)}")


def _app_init(intent_url: str, token: str) -> dict[str, Any]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "app.init",
            "params": {
                "scene": "web",
                "with_preload": False,
                "root_xmlid": "smart_construction_core.menu_sc_root",
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "app.init")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    return data


def _extract_role_summary(role: str, payload: dict[str, Any]) -> dict[str, Any]:
    workspace = payload.get("workspace_home") if isinstance(payload.get("workspace_home"), dict) else {}
    diagnostics = workspace.get("diagnostics") if isinstance(workspace.get("diagnostics"), dict) else {}
    stats = diagnostics.get("extraction_stats") if isinstance(diagnostics.get("extraction_stats"), dict) else {}
    ranking = diagnostics.get("action_ranking_policy") if isinstance(diagnostics.get("action_ranking_policy"), dict) else {}

    today_total = _to_int(stats.get("today_actions_total"))
    today_business = _to_int(stats.get("today_actions_business"))
    risk_total = _to_int(stats.get("risk_actions_total"))
    risk_business = _to_int(stats.get("risk_actions_business"))

    return {
        "role": role,
        "today_actions_total": today_total,
        "today_actions_business": today_business,
        "today_actions_business_rate": round((today_business / today_total) * 100, 2) if today_total > 0 else 0,
        "today_actions_factual": _to_int(stats.get("today_actions_factual")),
        "today_actions_factual_rate": round(_to_float(stats.get("today_actions_factual_rate")), 2),
        "risk_actions_total": risk_total,
        "risk_actions_business": risk_business,
        "risk_actions_business_rate": round((risk_business / risk_total) * 100, 2) if risk_total > 0 else 0,
        "risk_actions_factual": _to_int(stats.get("risk_actions_factual")),
        "risk_actions_factual_rate": round(_to_float(stats.get("risk_actions_factual_rate")), 2),
        "source_kind": _to_text(stats.get("source_kind") or ""),
        "fallback_reason": _to_text(stats.get("fallback_reason") or ""),
        "factual_extraction_hit_rate": round(_to_float(stats.get("factual_extraction_hit_rate")), 2),
        "business_rows_total": _to_int(stats.get("business_rows_total")),
        "business_collections": _to_int(stats.get("business_collections")),
        "ranking_policy": ranking,
    }


def _write_reports(report: dict[str, Any]) -> None:
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Workbench Extraction Hit-Rate Report",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- base_url: {report.get('base_url')}",
        f"- db_name: {report.get('db_name')}",
        f"- ok: {report.get('ok')}",
        "",
        "## Role Summary",
        "",
        "| role | source_kind | today_business_rate | today_factual_rate | risk_business_rate | risk_factual_rate | factual_hit_rate |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in report.get("roles", []):
        lines.append(
            f"| {item.get('role')} | {item.get('source_kind')} | {item.get('today_actions_business_rate')}% | {item.get('today_actions_factual_rate')}% | {item.get('risk_actions_business_rate')}% | {item.get('risk_actions_factual_rate')}% | {item.get('factual_extraction_hit_rate')}% |"
        )
    if report.get("errors"):
        lines.extend(["", "## Errors", ""])
        for err in report.get("errors", []):
            lines.append(f"- {err}")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    base_url = _to_text(os.getenv("E2E_BASE_URL") or get_base_url())
    intent_url = f"{base_url.rstrip('/')}/api/v1/intent"
    db_name = _to_text(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_demo")

    roles = _resolve_roles()
    role_reports: list[dict[str, Any]] = []
    errors: list[str] = []

    for role in roles:
        role_code = role["role"]
        login = role["login"]
        password_candidates = role.get("password_candidates") if isinstance(role.get("password_candidates"), list) else []
        if not login or not password_candidates:
            errors.append(f"{role_code}: missing login/password_candidates")
            continue
        try:
            token = _login(intent_url, db_name, login, password_candidates)
            app_init_payload = _app_init(intent_url, token)
            role_reports.append(_extract_role_summary(role_code, app_init_payload))
        except Exception as exc:
            errors.append(f"{role_code}({login}): {exc}")

    report = {
        "ok": len(role_reports) > 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "db_name": db_name,
        "roles": role_reports,
        "errors": errors,
    }
    _write_reports(report)
    print(str(REPORT_JSON))
    print(str(REPORT_MD))
    if report["ok"]:
        print(f"[workbench_extraction_hit_rate_report] PASS roles={len(role_reports)}")
        return 0
    print("[workbench_extraction_hit_rate_report] FAIL no successful role reports")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
