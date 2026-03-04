#!/usr/bin/env python3
"""Baseline policy guard for grouped governance brief metrics."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_brief_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_brief_baseline_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def _coverage_ratio_to_float(raw: Any) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    if not isinstance(raw, str) or "/" not in raw:
        return 0.0
    left, right = raw.split("/", 1)
    left_i = _to_int(left)
    right_i = _to_int(right)
    if right_i <= 0:
        return 0.0
    return float(left_i) / float(right_i)


def main() -> int:
    policy = _load_json(BASELINE_JSON)
    if not policy:
        print("[grouped_governance_brief_baseline_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[grouped_governance_brief_baseline_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    trend = report.get("trend") if isinstance(report.get("trend"), dict) else {}
    delta = trend.get("delta") if isinstance(trend.get("delta"), dict) else {}
    has_previous = bool(trend.get("has_previous"))

    if bool(policy.get("require_ok", True)) and not bool(report.get("ok")):
        errors.append("grouped_governance_brief_guard.ok must be true")
    if bool(policy.get("require_contract_governance_coverage_ok", True)) and not bool(
        ((report.get("checks") or {}).get("contract_governance_coverage_ok"))
    ):
        errors.append("checks.contract_governance_coverage_ok must be true")
    if bool(policy.get("require_grouped_drift_summary_ok", True)) and not bool(
        ((report.get("checks") or {}).get("grouped_drift_summary_ok"))
    ):
        errors.append("checks.grouped_drift_summary_ok must be true")

    min_governance_coverage_ratio = float(policy.get("min_governance_coverage_ratio", 1.0) or 1.0)
    if _coverage_ratio_to_float(summary.get("governance_coverage_ratio")) < min_governance_coverage_ratio:
        errors.append(f"summary.governance_coverage_ratio must be >= {min_governance_coverage_ratio}")

    max_governance_failure_count = int(policy.get("max_governance_failure_count", 0) or 0)
    if _to_int(summary.get("governance_failure_count")) > max_governance_failure_count:
        errors.append(f"summary.governance_failure_count must be <= {max_governance_failure_count}")

    min_grouped_e2e_case_count = int(policy.get("min_grouped_e2e_case_count", 1) or 1)
    if _to_int(summary.get("grouped_e2e_case_count")) < min_grouped_e2e_case_count:
        errors.append(f"summary.grouped_e2e_case_count must be >= {min_grouped_e2e_case_count}")

    min_grouped_e2e_grouped_rows_case_count = int(policy.get("min_grouped_e2e_grouped_rows_case_count", 0) or 0)
    if _to_int(summary.get("grouped_e2e_grouped_rows_case_count")) < min_grouped_e2e_grouped_rows_case_count:
        errors.append(
            f"summary.grouped_e2e_grouped_rows_case_count must be >= {min_grouped_e2e_grouped_rows_case_count}"
        )

    min_grouped_e2e_max_consistency_score = int(policy.get("min_grouped_e2e_max_consistency_score", 0) or 0)
    if _to_int(summary.get("grouped_e2e_max_consistency_score")) < min_grouped_e2e_max_consistency_score:
        errors.append(
            f"summary.grouped_e2e_max_consistency_score must be >= {min_grouped_e2e_max_consistency_score}"
        )

    if bool(policy.get("require_grouped_export_marker_full_hit", True)):
        hits = _to_int(summary.get("grouped_export_marker_hits"))
        total = _to_int(summary.get("grouped_export_marker_total"))
        if hits != total:
            errors.append("summary.grouped_export_marker_hits must equal summary.grouped_export_marker_total")

    if bool(policy.get("forbid_coverage_ratio_regression", True)):
        cov_delta = delta.get("governance_coverage_ratio_delta")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(
            cov_delta, (int, float)
        ):
            errors.append("trend.delta.governance_coverage_ratio_delta must be numeric when has_previous=true")
        elif isinstance(cov_delta, (int, float)) and float(cov_delta) < 0:
            errors.append("trend.delta.governance_coverage_ratio_delta must be >= 0")

    if bool(policy.get("forbid_governance_failure_count_increase", True)):
        failure_delta = delta.get("governance_failure_count")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(failure_delta, int):
            errors.append("trend.delta.governance_failure_count must be int when has_previous=true")
        elif isinstance(failure_delta, int) and failure_delta > 0:
            errors.append("trend.delta.governance_failure_count must be <= 0")

    if bool(policy.get("forbid_grouped_consistency_score_regression", True)):
        consistency_delta = delta.get("grouped_e2e_max_consistency_score")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(
            consistency_delta, int
        ):
            errors.append("trend.delta.grouped_e2e_max_consistency_score must be int when has_previous=true")
        elif isinstance(consistency_delta, int) and consistency_delta < 0:
            errors.append("trend.delta.grouped_e2e_max_consistency_score must be >= 0")

    if bool(policy.get("forbid_grouped_e2e_case_count_regression", False)):
        e2e_case_delta = delta.get("grouped_e2e_case_count")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(e2e_case_delta, int):
            errors.append("trend.delta.grouped_e2e_case_count must be int when has_previous=true")
        elif isinstance(e2e_case_delta, int) and e2e_case_delta < 0:
            errors.append("trend.delta.grouped_e2e_case_count must be >= 0")

    if bool(policy.get("forbid_grouped_rows_case_count_regression", False)):
        grouped_rows_case_delta = delta.get("grouped_e2e_grouped_rows_case_count")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(
            grouped_rows_case_delta, int
        ):
            errors.append("trend.delta.grouped_e2e_grouped_rows_case_count must be int when has_previous=true")
        elif isinstance(grouped_rows_case_delta, int) and grouped_rows_case_delta < 0:
            errors.append("trend.delta.grouped_e2e_grouped_rows_case_count must be >= 0")

    if bool(policy.get("forbid_grouped_export_marker_hits_regression", False)):
        marker_hits_delta = delta.get("grouped_export_marker_hits")
        if has_previous and bool(policy.get("require_trend_delta_when_previous", True)) and not isinstance(
            marker_hits_delta, int
        ):
            errors.append("trend.delta.grouped_export_marker_hits must be int when has_previous=true")
        elif isinstance(marker_hits_delta, int) and marker_hits_delta < 0:
            errors.append("trend.delta.grouped_export_marker_hits must be >= 0")

    if errors:
        print("[grouped_governance_brief_baseline_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_governance_brief_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
