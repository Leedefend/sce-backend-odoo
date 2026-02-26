#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAP_USAGE_JSON = ROOT / "artifacts" / "backend" / "capability_usage_matrix.json"
SCENE_DOMAIN_JSON = ROOT / "artifacts" / "backend" / "scene_domain_mapping.json"
BUTTON_SEM_JSON = ROOT / "artifacts" / "backend" / "button_semantic_report.json"
ROLE_DIFF_JSON = ROOT / "artifacts" / "backend" / "role_capability_diff_report.json"
TREND_JSON = ROOT / "artifacts" / "backend" / "runtime_trend_report.json"
EXPLAIN_JSON = ROOT / "artifacts" / "backend" / "catalog_runtime_explain_report.json"
SEMANTIC_JSON = ROOT / "artifacts" / "backend" / "semantic_behavior_guard_report.json"
WEEK1_JSON = ROOT / "artifacts" / "backend" / "sprint_week1_audit_report.json"
WEEK2_JSON = ROOT / "artifacts" / "backend" / "sprint_week2_final_report.json"
STRESS_JSON = ROOT / "artifacts" / "backend" / "system_stability_stress_regression_report.json"

REPORT_JSON = ROOT / "artifacts" / "backend" / "phasex_operating_summary_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "phasex_operating_summary_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _int(path_obj: dict, *keys: str) -> int:
    cur = path_obj
    for k in keys:
        cur = cur.get(k) if isinstance(cur, dict) else None
    try:
        return int(cur or 0)
    except Exception:
        return 0


def _str(path_obj: dict, *keys: str) -> str:
    cur = path_obj
    for k in keys:
        cur = cur.get(k) if isinstance(cur, dict) else None
    return str(cur or "").strip()


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    cap = _load(CAP_USAGE_JSON)
    scene = _load(SCENE_DOMAIN_JSON)
    button = _load(BUTTON_SEM_JSON)
    role = _load(ROLE_DIFF_JSON)
    trend = _load(TREND_JSON)
    explain = _load(EXPLAIN_JSON)
    semantic = _load(SEMANTIC_JSON)
    week1 = _load(WEEK1_JSON)
    week2 = _load(WEEK2_JSON)
    stress = _load(STRESS_JSON)

    for name, obj in [
        ("capability_usage", cap),
        ("scene_domain", scene),
        ("button_semantic", button),
        ("role_diff", role),
        ("runtime_trend", trend),
        ("catalog_runtime_explain", explain),
        ("semantic_guard", semantic),
        ("week1", week1),
        ("week2", week2),
        ("stress", stress),
    ]:
        if not obj:
            errors.append(f"missing_report={name}")

    snapshot = {
        "capability_count": _int(cap, "summary", "capability_count"),
        "isolated_capability_count": _int(cap, "summary", "isolated_count"),
        "unresolved_intent_count": _int(cap, "summary", "unresolved_intent_count"),
        "runtime_scene_count": _int(scene, "summary", "runtime_scene_count"),
        "domain_count": _int(scene, "summary", "domain_count"),
        "unknown_domain_count": _int(scene, "summary", "unknown_domain_count"),
        "unclassified_404_count": _int(button, "summary", "unclassified_404_count"),
        "role_sample_count": _int(role, "summary", "role_sample_count"),
        "over_authorized_profile_count": _int(role, "summary", "over_authorized_profile_count"),
        "trend_days": _int(trend, "summary", "window_days"),
        "trend_history_day_count": _int(trend, "summary", "history_day_count"),
        "unknown_source_count": _int(explain, "summary", "unknown_source_count"),
        "semantic_drift_count": _int(semantic, "summary", "drift_count"),
        "week1_error_count": _int(week1, "summary", "error_count"),
        "week2_error_count": _int(week2, "summary", "error_count"),
        "stress_status": _str(stress, "status"),
        "stress_error_count": _int(stress, "summary", "error_count"),
        "stress_warning_count": _int(stress, "summary", "warning_count"),
    }

    gates = {
        "capability_explainable": snapshot["unresolved_intent_count"] == 0,
        "scene_fully_assigned": snapshot["unknown_domain_count"] == 0,
        "button_404_fully_classified": snapshot["unclassified_404_count"] == 0,
        "role_sample_ready": snapshot["role_sample_count"] >= 8 and snapshot["over_authorized_profile_count"] == 0,
        "runtime_source_explained": snapshot["unknown_source_count"] == 0,
        "semantic_guard_clean": snapshot["semantic_drift_count"] == 0,
        "week1_gate_clean": snapshot["week1_error_count"] == 0,
        "week2_gate_clean": snapshot["week2_error_count"] == 0,
        "stress_no_errors": snapshot["stress_error_count"] == 0,
    }
    if not gates["capability_explainable"]:
        errors.append("capability explainability gate failed")
    if not gates["button_404_fully_classified"]:
        errors.append("button semantic gate failed")
    if not gates["scene_fully_assigned"]:
        errors.append("scene assignment gate failed")
    if not gates["role_sample_ready"]:
        errors.append("role coverage/authorization gate failed")
    if not gates["runtime_source_explained"]:
        errors.append("catalog-runtime explain gate failed")
    if not gates["semantic_guard_clean"]:
        errors.append("semantic drift gate failed")
    if not gates["week1_gate_clean"] or not gates["week2_gate_clean"]:
        errors.append("sprint milestone gate failed")
    if not gates["stress_no_errors"]:
        errors.append("stress error gate failed")
    if snapshot["stress_status"] == "warn":
        warnings.append("stress status WARN")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "gate_count": len(gates),
            "gate_pass_count": sum(1 for x in gates.values() if x),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "snapshot": snapshot,
        "gates": gates,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Phase X Operating Summary Report",
        "",
        f"- gate_pass_count: {payload['summary']['gate_pass_count']}/{payload['summary']['gate_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "## Snapshot",
        "",
    ]
    for key in sorted(snapshot):
        lines.append(f"- {key}: {snapshot[key]}")
    lines.extend(["", "## Gates", ""])
    for key in sorted(gates):
        lines.append(f"- {key}: {'PASS' if gates[key] else 'FAIL'}")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[phasex_operating_summary_report] FAIL")
        return 2
    print("[phasex_operating_summary_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
