#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs" / "product" / "system_user_experience_coverage_v1.json"
PLAN = ROOT / "docs" / "product" / "system_user_experience_iteration_plan_v1.md"

REQUIRED_ROLE_CODES = {"executive", "project_manager", "finance", "business_operator", "config_admin", "support_operator"}
REQUIRED_SURFACE_TYPES = {"login", "home", "navigation", "dashboard", "workspace", "list", "form", "detail", "admin", "support", "mobile"}
REQUIRED_PAGE_MODES = {"dashboard", "workspace", "list", "form", "detail", "admin"}
REQUIRED_ISSUE_CODES = {"IA", "TASK", "STRUCTURE", "LANGUAGE", "DATA", "PERFORMANCE", "MOBILE", "ACCESS"}
REQUIRED_GATES = {
    "verify.product.page_structure",
    "verify.product.navigation_boundary",
    "verify.business_system.usability_readiness",
    "verify.business_config.config_workbench_operation_local_closeout",
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"[system_user_experience_coverage_guard] missing {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("[system_user_experience_coverage_guard] matrix must be an object")
    return payload


def _as_list(payload: dict, key: str) -> list:
    value = payload.get(key)
    return value if isinstance(value, list) else []


def _codes(rows: list, key: str) -> set[str]:
    return {str(row.get(key, "")).strip() for row in rows if isinstance(row, dict) and row.get(key)}


def main() -> int:
    errors: list[str] = []
    payload = _load_json(MATRIX)
    thresholds = payload.get("coverage_thresholds") if isinstance(payload.get("coverage_thresholds"), dict) else {}

    roles = _as_list(payload, "roles")
    journeys = _as_list(payload, "journeys")
    surface_types = {str(item).strip() for item in _as_list(payload, "surface_types")}
    page_modes = {str(item).strip() for item in _as_list(payload, "page_modes")}
    issue_codes = _codes(_as_list(payload, "issue_taxonomy"), "code")
    gates = {str(item).strip() for item in _as_list(payload, "acceptance_gates")}

    role_codes = _codes(roles, "code")
    journey_roles = _codes(journeys, "role")
    journey_surface_types = _codes(journeys, "surface_type")
    journey_page_modes = _codes(journeys, "page_mode")
    user_action_count = sum(len(row.get("actions") or []) for row in journeys if isinstance(row, dict))
    automated_evidence = {
        str(item).strip()
        for row in journeys
        if isinstance(row, dict)
        for item in (row.get("automated_evidence") or [])
        if str(item).strip()
    }
    browser_evidence_count = sum(1 for row in journeys if isinstance(row, dict) and row.get("browser_evidence") is True)

    if not REQUIRED_ROLE_CODES.issubset(role_codes):
        errors.append(f"missing required roles: {sorted(REQUIRED_ROLE_CODES - role_codes)}")
    if not REQUIRED_ROLE_CODES.issubset(journey_roles):
        errors.append(f"journeys missing required roles: {sorted(REQUIRED_ROLE_CODES - journey_roles)}")
    if not REQUIRED_SURFACE_TYPES.issubset(surface_types):
        errors.append(f"missing required surface types: {sorted(REQUIRED_SURFACE_TYPES - surface_types)}")
    if not {"home", "navigation", "list", "form", "admin", "mobile"}.issubset(journey_surface_types):
        errors.append("journeys must include home, navigation, list, form, admin, and mobile-oriented coverage")
    if not REQUIRED_PAGE_MODES.issubset(page_modes):
        errors.append(f"missing required page modes: {sorted(REQUIRED_PAGE_MODES - page_modes)}")
    if not REQUIRED_PAGE_MODES.issubset(journey_page_modes):
        errors.append(f"journeys missing page modes: {sorted(REQUIRED_PAGE_MODES - journey_page_modes)}")
    if not REQUIRED_ISSUE_CODES.issubset(issue_codes):
        errors.append(f"missing issue taxonomy: {sorted(REQUIRED_ISSUE_CODES - issue_codes)}")
    if not REQUIRED_GATES.issubset(gates):
        errors.append(f"missing required gates: {sorted(REQUIRED_GATES - gates)}")

    checks = {
        "roles": len(role_codes),
        "journeys": len(journeys),
        "surface_types": len(surface_types),
        "page_modes": len(page_modes),
        "user_actions": user_action_count,
        "automated_evidence": len(automated_evidence),
        "browser_evidence": browser_evidence_count,
    }
    for key, observed in checks.items():
        threshold_key = f"min_{key}"
        expected = int(thresholds.get(threshold_key) or 0)
        if observed < expected:
            errors.append(f"{key} {observed} < {threshold_key} {expected}")

    plan_text = PLAN.read_text(encoding="utf-8") if PLAN.is_file() else ""
    for token in ("覆盖矩阵", "浏览器走查", "批量优化", "收口门禁"):
        if token not in plan_text:
            errors.append(f"plan missing token: {token}")

    if errors:
        print("[system_user_experience_coverage_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 2

    print(
        "[system_user_experience_coverage_guard] PASS "
        f"roles={checks['roles']} journeys={checks['journeys']} "
        f"surface_types={checks['surface_types']} page_modes={checks['page_modes']} "
        f"user_actions={checks['user_actions']} automated_evidence={checks['automated_evidence']} "
        f"browser_evidence={checks['browser_evidence']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
