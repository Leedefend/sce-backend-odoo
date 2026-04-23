#!/usr/bin/env python3
"""Schema guard for grouped governance trend consistency report."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_trend_consistency_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_trend_consistency_schema_guard.json"


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
        print("[grouped_governance_trend_consistency_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1
    report = _load_json(REPORT_JSON)
    if not report:
        print("[grouped_governance_trend_consistency_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    required_top_keys = baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else []
    required_summary_keys = baseline.get("required_summary_keys") if isinstance(
        baseline.get("required_summary_keys"), list
    ) else []
    summary_key_types = baseline.get("summary_key_types") if isinstance(baseline.get("summary_key_types"), dict) else {}
    for key in required_top_keys:
        key = str(key).strip()
        if key and key not in report:
            errors.append(f"missing top-level key: {key}")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    has_previous_brief = bool(summary.get("has_previous_brief")) if isinstance(summary, dict) else False
    has_previous_matrix = bool(summary.get("has_previous_matrix")) if isinstance(summary, dict) else False
    for key in required_summary_keys:
        key = str(key).strip()
        if key and key not in summary:
            errors.append(f"missing summary key: {key}")
    for key, expected in summary_key_types.items():
        key = str(key).strip()
        expected = str(expected).strip()
        value = summary.get(key) if key in summary else None
        if value is None and key.startswith("brief_delta_") and not has_previous_brief:
            continue
        if value is None and key.startswith("matrix_delta_") and not has_previous_matrix:
            continue
        if key and key in summary and expected and not _type_ok(value, expected):
            errors.append(f"summary.{key} must be {expected}")

    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    if not isinstance(report.get("errors"), list):
        errors.append("errors must be list")
    if not isinstance(report.get("policy"), dict):
        errors.append("policy must be object")
    report_paths = report.get("report") if isinstance(report.get("report"), dict) else {}
    report_json = str(report_paths.get("json") or "").strip()
    report_md = str(report_paths.get("md") or "").strip()
    if not report_json:
        errors.append("report.json must be non-empty")
    if not report_md:
        errors.append("report.md must be non-empty")
    json_prefix = str(baseline.get("report_json_prefix") or "").strip()
    json_suffix = str(baseline.get("report_json_suffix") or "").strip()
    md_prefix = str(baseline.get("report_md_prefix") or "").strip()
    md_suffix = str(baseline.get("report_md_suffix") or "").strip()
    if json_prefix and report_json and not report_json.startswith(json_prefix):
        errors.append("report.json must start with " + json_prefix)
    if json_suffix and report_json and not report_json.endswith(json_suffix):
        errors.append("report.json must end with " + json_suffix)
    if md_prefix and report_md and not report_md.startswith(md_prefix):
        errors.append("report.md must start with " + md_prefix)
    if md_suffix and report_md and not report_md.endswith(md_suffix):
        errors.append("report.md must end with " + md_suffix)

    if errors:
        print("[grouped_governance_trend_consistency_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1
    print("[grouped_governance_trend_consistency_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
