#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "business_capability_baseline_report.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def main() -> int:
    report = _load_json(REPORT_JSON)
    if not report:
        print("[business_capability_baseline_report_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    if not isinstance(report.get("ok"), bool):
        errors.append("ok must be bool")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    baseline_snapshot = report.get("baseline_snapshot") if isinstance(report.get("baseline_snapshot"), dict) else {}
    delta = report.get("delta_vs_baseline") if isinstance(report.get("delta_vs_baseline"), dict) else {}
    checks = report.get("checks") if isinstance(report.get("checks"), list) else None
    if not summary:
        errors.append("summary must be object")
    if not baseline_snapshot:
        errors.append("baseline_snapshot must be object")
    if not delta:
        errors.append("delta_vs_baseline must be object")
    if checks is None:
        errors.append("checks must be list")
        checks = []

    for key in (
        "check_count",
        "failed_check_count",
        "error_count",
        "required_intent_count",
        "required_role_count",
        "catalog_runtime_ratio",
    ):
        if key not in summary:
            errors.append(f"summary missing key: {key}")
    for key in ("check_count", "required_intent_count", "required_role_count", "catalog_runtime_ratio"):
        if key not in baseline_snapshot:
            errors.append(f"baseline_snapshot missing key: {key}")
        if key not in delta:
            errors.append(f"delta_vs_baseline missing key: {key}")

    if _safe_int(summary.get("check_count"), -1) != len(checks):
        errors.append("summary.check_count mismatch with checks length")

    names = [str(row.get("name") or "") for row in checks if isinstance(row, dict)]
    if names != sorted(names):
        errors.append("checks must be sorted by name for deterministic diff")

    if errors:
        print("[business_capability_baseline_report_schema_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[business_capability_baseline_report_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
