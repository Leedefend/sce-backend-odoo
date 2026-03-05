#!/usr/bin/env python3
"""Schema guard for grouped governance policy matrix artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_policy_matrix.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_policy_matrix_schema_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "bool":
        return isinstance(value, bool)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str) and bool(value.strip())
    return True


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[grouped_governance_policy_matrix_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[grouped_governance_policy_matrix_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    required_top_keys = baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else []
    required_summary_keys = baseline.get("required_summary_keys") if isinstance(baseline.get("required_summary_keys"), list) else []
    required_policy_groups = baseline.get("required_policy_groups") if isinstance(baseline.get("required_policy_groups"), list) else []
    required_trend_delta_keys = baseline.get("required_trend_delta_keys") if isinstance(
        baseline.get("required_trend_delta_keys"), list
    ) else []
    summary_key_types = baseline.get("summary_key_types") if isinstance(baseline.get("summary_key_types"), dict) else {}
    trend_delta_key_types = baseline.get("trend_delta_key_types") if isinstance(baseline.get("trend_delta_key_types"), dict) else {}

    for key in required_top_keys:
        key = str(key).strip()
        if key and key not in report:
            errors.append(f"missing top-level key: {key}")

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    for key in required_summary_keys:
        key = str(key).strip()
        if key and key not in summary:
            errors.append(f"missing summary key: {key}")
    for key, expected in summary_key_types.items():
        key = str(key).strip()
        expected = str(expected).strip()
        if key and key in summary and expected and not _type_ok(summary.get(key), expected):
            errors.append(f"summary.{key} must be {expected}")

    policy_groups = report.get("policy_groups") if isinstance(report.get("policy_groups"), dict) else {}
    for key in required_policy_groups:
        key = str(key).strip()
        if key and not isinstance(policy_groups.get(key), dict):
            errors.append(f"policy_groups.{key} must be object")

    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    if not isinstance(report.get("errors"), list):
        errors.append("errors must be list")
    if not isinstance(report.get("sources"), dict):
        errors.append("sources must be object")
    trend = report.get("trend") if isinstance(report.get("trend"), dict) else {}
    delta = trend.get("delta") if isinstance(trend.get("delta"), dict) else {}
    for key in required_trend_delta_keys:
        key = str(key).strip()
        if key and key not in delta:
            errors.append(f"trend.delta missing key: {key}")
    if "trend" in report and not isinstance(report.get("trend"), dict):
        errors.append("trend must be object")
    if trend and not isinstance(trend.get("has_previous"), bool):
        errors.append("trend.has_previous must be bool")
    if bool(baseline.get("enforce_trend_delta_types_when_previous", True)) and bool(trend.get("has_previous")):
        for key, expected in trend_delta_key_types.items():
            key = str(key).strip()
            expected = str(expected).strip()
            if key and key in delta and expected and not _type_ok(delta.get(key), expected):
                errors.append(f"trend.delta.{key} must be {expected} when has_previous=true")

    report_json = str(summary.get("report_json") or "").strip()
    report_md = str(summary.get("report_md") or "").strip()
    summary_json_prefix = str(baseline.get("summary_report_json_prefix") or "").strip()
    summary_json_suffix = str(baseline.get("summary_report_json_suffix") or "").strip()
    summary_md_prefix = str(baseline.get("summary_report_md_prefix") or "").strip()
    summary_md_suffix = str(baseline.get("summary_report_md_suffix") or "").strip()
    if summary_json_prefix and report_json and not report_json.startswith(summary_json_prefix):
        errors.append("summary.report_json must start with " + summary_json_prefix)
    if summary_json_suffix and report_json and not report_json.endswith(summary_json_suffix):
        errors.append("summary.report_json must end with " + summary_json_suffix)
    if summary_md_prefix and report_md and not report_md.startswith(summary_md_prefix):
        errors.append("summary.report_md must start with " + summary_md_prefix)
    if summary_md_suffix and report_md and not report_md.endswith(summary_md_suffix):
        errors.append("summary.report_md must end with " + summary_md_suffix)

    if errors:
        print("[grouped_governance_policy_matrix_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_governance_policy_matrix_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
