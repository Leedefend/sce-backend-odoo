#!/usr/bin/env python3
"""Baseline guard for grouped governance trend consistency report."""

from __future__ import annotations

import json
from pathlib import Path
import sys


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

    if bool(policy.get("require_ok", True)) and not bool(report.get("ok")):
        errors.append("grouped_governance_trend_consistency_guard.ok must be true")
    if bool(policy.get("require_has_previous_aligned", True)) and not bool(summary.get("has_previous_aligned")):
        errors.append("summary.has_previous_aligned must be true")
    if bool(policy.get("require_delta_types_ok", True)):
        if not bool(summary.get("brief_delta_types_ok")):
            errors.append("summary.brief_delta_types_ok must be true")
        if not bool(summary.get("matrix_delta_types_ok")):
            errors.append("summary.matrix_delta_types_ok must be true")

    if errors:
        print("[grouped_governance_trend_consistency_baseline_guard] FAIL")
        for line in errors:
            print(line)
        return 1
    print("[grouped_governance_trend_consistency_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
