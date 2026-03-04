#!/usr/bin/env python3
"""Baseline guard for grouped governance trend consistency report."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_trend_consistency_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_trend_consistency_baseline_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except Exception:
            return None
    return None


def main() -> int:
    policy = _load_json(BASELINE_JSON)
    if not policy:
        print("[grouped_governance_trend_consistency_baseline_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1
    report = _load_json(REPORT_JSON)
    if not report:
        print("[grouped_governance_trend_consistency_baseline_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    report_paths = report.get("report") if isinstance(report.get("report"), dict) else {}

    if bool(policy.get("require_ok", True)) and not bool(report.get("ok")):
        errors.append("grouped_governance_trend_consistency_guard.ok must be true")
    if bool(policy.get("require_has_previous_aligned", True)) and not bool(summary.get("has_previous_aligned")):
        errors.append("summary.has_previous_aligned must be true")
    if bool(policy.get("require_delta_types_ok", True)):
        if not bool(summary.get("brief_delta_types_ok")):
            errors.append("summary.brief_delta_types_ok must be true")
        if not bool(summary.get("matrix_delta_types_ok")):
            errors.append("summary.matrix_delta_types_ok must be true")
    if bool(policy.get("require_has_previous_pair_bool", True)):
        if not isinstance(summary.get("has_previous_brief"), bool):
            errors.append("summary.has_previous_brief must be bool")
        if not isinstance(summary.get("has_previous_matrix"), bool):
            errors.append("summary.has_previous_matrix must be bool")

    report_json = str(report_paths.get("json") or "").strip()
    report_md = str(report_paths.get("md") or "").strip()
    report_json_prefix = str(policy.get("require_report_json_prefix") or "").strip()
    report_json_suffix = str(policy.get("require_report_json_suffix") or "").strip()
    report_md_prefix = str(policy.get("require_report_md_prefix") or "").strip()
    report_md_suffix = str(policy.get("require_report_md_suffix") or "").strip()
    if report_json_prefix and not report_json.startswith(report_json_prefix):
        errors.append("report.json must start with " + report_json_prefix)
    if report_json_suffix and not report_json.endswith(report_json_suffix):
        errors.append("report.json must end with " + report_json_suffix)
    if report_md_prefix and not report_md.startswith(report_md_prefix):
        errors.append("report.md must start with " + report_md_prefix)
    if report_md_suffix and not report_md.endswith(report_md_suffix):
        errors.append("report.md must end with " + report_md_suffix)

    has_previous_brief = bool(summary.get("has_previous_brief"))
    has_previous_matrix = bool(summary.get("has_previous_matrix"))
    if bool(policy.get("require_delta_typed_when_previous", True)) and (has_previous_brief or has_previous_matrix):
        if not isinstance(_to_float(summary.get("brief_delta_governance_coverage_ratio")), float):
            errors.append("summary.brief_delta_governance_coverage_ratio must be numeric when has_previous=true")
        if not isinstance(_to_int(summary.get("brief_delta_governance_failure_count")), int):
            errors.append("summary.brief_delta_governance_failure_count must be int when has_previous=true")
        if not isinstance(_to_int(summary.get("brief_delta_grouped_e2e_max_consistency_score")), int):
            errors.append("summary.brief_delta_grouped_e2e_max_consistency_score must be int when has_previous=true")
        if not isinstance(_to_int(summary.get("matrix_delta_grouped_governance_brief_policy_count")), int):
            errors.append("summary.matrix_delta_grouped_governance_brief_policy_count must be int when has_previous=true")
        if not isinstance(_to_int(summary.get("matrix_delta_grouped_drift_summary_policy_count")), int):
            errors.append("summary.matrix_delta_grouped_drift_summary_policy_count must be int when has_previous=true")
        if not isinstance(_to_int(summary.get("matrix_delta_contract_evidence_grouped_governance_policy_count")), int):
            errors.append(
                "summary.matrix_delta_contract_evidence_grouped_governance_policy_count must be int when has_previous=true"
            )

    if errors:
        print("[grouped_governance_trend_consistency_baseline_guard] FAIL")
        for line in errors:
            print(line)
        return 1
    print("[grouped_governance_trend_consistency_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
