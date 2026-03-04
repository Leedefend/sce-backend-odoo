#!/usr/bin/env python3
"""Baseline policy guard for grouped drift summary report metrics."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_drift_summary_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_drift_summary_baseline_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    policy = _load_json(BASELINE_JSON)
    if not policy:
        print("[grouped_drift_summary_baseline_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[grouped_drift_summary_baseline_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}

    require_ok = bool(policy.get("require_ok", True))
    if require_ok and not bool(report.get("ok")):
        errors.append("grouped_drift_summary_guard.ok must be true")

    min_e2e_case_count = int(policy.get("min_e2e_case_count", 1) or 1)
    if int(summary.get("e2e_case_count") or 0) < min_e2e_case_count:
        errors.append(f"summary.e2e_case_count must be >= {min_e2e_case_count}")

    min_grouped_rows_case_count = int(policy.get("min_e2e_grouped_rows_case_count", 0) or 0)
    if int(summary.get("e2e_grouped_rows_case_count") or 0) < min_grouped_rows_case_count:
        errors.append(f"summary.e2e_grouped_rows_case_count must be >= {min_grouped_rows_case_count}")

    min_max_consistency_score = int(policy.get("min_e2e_max_consistency_score", 0) or 0)
    if int(summary.get("e2e_max_consistency_score") or 0) < min_max_consistency_score:
        errors.append(f"summary.e2e_max_consistency_score must be >= {min_max_consistency_score}")

    require_export_marker_full_hit = bool(policy.get("require_export_marker_full_hit", True))
    hits = int(summary.get("export_marker_hits") or 0)
    total = int(summary.get("export_marker_total") or 0)
    if require_export_marker_full_hit and hits != total:
        errors.append("summary.export_marker_hits must equal summary.export_marker_total")

    require_grouped_field_checks_all_true = bool(policy.get("require_grouped_field_checks_all_true", True))
    grouped_field_checks = summary.get("grouped_field_checks") if isinstance(summary.get("grouped_field_checks"), dict) else {}
    if require_grouped_field_checks_all_true:
        for key in ("group_key", "page_has_prev", "page_has_next", "page_window"):
            if grouped_field_checks.get(key) is not True:
                errors.append(f"summary.grouped_field_checks.{key} must be true")

    if errors:
        print("[grouped_drift_summary_baseline_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_drift_summary_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
