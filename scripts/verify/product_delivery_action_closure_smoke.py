#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "artifacts" / "backend" / "scene_contract_v1_field_schema_state.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_action_closure_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_action_closure_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _find_scene(scenes: list, scene_key: str) -> dict:
    for row in scenes:
        item = _as_dict(row)
        scene = _as_dict(item.get("scene"))
        if str(scene.get("key") or "").strip() == scene_key:
            return item
    return {}


def _check_payment_request(scene_row: dict) -> list[str]:
    issues: list[str] = []
    action_surface = _as_dict(scene_row.get("action_surface"))
    primary_actions = _as_list(action_surface.get("primary_actions"))
    if len(primary_actions) < 1:
        issues.append("primary_actions<1")

    workflow_surface = _as_dict(scene_row.get("workflow_surface"))
    states = _as_list(workflow_surface.get("states"))
    if len(states) < 1:
        issues.append("workflow_states<1")

    search_surface = _as_dict(scene_row.get("search_surface"))
    filters = _as_list(search_surface.get("filters"))
    if len(filters) < 1:
        issues.append("search_filters<1")
    return issues


def _check_projects_list(scene_row: dict) -> list[str]:
    issues: list[str] = []
    search_surface = _as_dict(scene_row.get("search_surface"))
    filters = _as_list(search_surface.get("filters"))
    if len(filters) < 1:
        issues.append("search_filters<1")

    group_by = _as_list(search_surface.get("group_by"))
    if len(group_by) < 1:
        issues.append("group_by<1")

    action_surface = _as_dict(scene_row.get("action_surface"))
    if str(action_surface.get("selection_mode") or "").strip() == "":
        issues.append("selection_mode_missing")
    return issues


def _check_project_budget(scene_row: dict) -> list[str]:
    issues: list[str] = []
    search_surface = _as_dict(scene_row.get("search_surface"))
    filters = _as_list(search_surface.get("filters"))
    if len(filters) < 1:
        issues.append("search_filters<1")

    action_surface = _as_dict(scene_row.get("action_surface"))
    groups = _as_list(action_surface.get("groups"))
    if len(groups) < 1:
        issues.append("action_groups<1")

    validation_surface = _as_dict(scene_row.get("validation_surface"))
    field_rules = _as_dict(validation_surface.get("field_rules"))
    if len(field_rules) < 1:
        issues.append("validation_field_rules<1")
    return issues


def main() -> int:
    errors: list[str] = []
    checks: list[dict] = []

    payload = _load_json(STATE_PATH)
    contract = _as_dict(payload.get("scene_ready_contract_v1"))
    scenes = _as_list(contract.get("scenes"))
    if not scenes:
        errors.append("scene_ready_contract_v1.scenes is empty")

    targets = [
        ("finance.payment_requests", "付款申请与审批", _check_payment_request),
        ("projects.list", "项目台账", _check_projects_list),
        ("cost.project_budget", "预算管理", _check_project_budget),
    ]

    for scene_key, label, checker in targets:
        row = _find_scene(scenes, scene_key)
        if not row:
            checks.append({"scene_key": scene_key, "label": label, "ok": False, "issues": ["scene_missing"]})
            continue
        issues = checker(row)
        checks.append({"scene_key": scene_key, "label": label, "ok": len(issues) == 0, "issues": issues})

    failed = [item for item in checks if not bool(item.get("ok"))]
    if failed:
        errors.append(f"action_closure_failed_count={len(failed)}")

    report = {
        "ok": len(errors) == 0,
        "summary": {
            "target_count": len(targets),
            "pass_count": len(checks) - len(failed),
            "failed_count": len(failed),
            "error_count": len(errors),
        },
        "checks": checks,
        "errors": errors,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Product Delivery Action Closure Smoke",
        "",
        f"- target_count: {report['summary']['target_count']}",
        f"- pass_count: {report['summary']['pass_count']}",
        f"- failed_count: {report['summary']['failed_count']}",
        f"- error_count: {report['summary']['error_count']}",
        "",
        "## Checks",
        "",
    ]
    for item in checks:
        status = "PASS" if item.get("ok") else "FAIL"
        issues = ",".join(item.get("issues") or []) or "-"
        lines.append(f"- {item.get('label')} ({item.get('scene_key')}): {status} issues={issues}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(REPORT_JSON)
    print(REPORT_MD)
    if errors:
        print("[product_delivery_action_closure_smoke] FAIL")
        return 2
    print("[product_delivery_action_closure_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

