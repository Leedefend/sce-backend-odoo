#!/usr/bin/env python3
"""Schema guard for grouped governance policy matrix artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


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

    for key in required_top_keys:
        key = str(key).strip()
        if key and key not in report:
            errors.append(f"missing top-level key: {key}")

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    for key in required_summary_keys:
        key = str(key).strip()
        if key and key not in summary:
            errors.append(f"missing summary key: {key}")

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

    if errors:
        print("[grouped_governance_policy_matrix_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_governance_policy_matrix_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
