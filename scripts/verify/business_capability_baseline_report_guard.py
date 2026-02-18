#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "business_capability_baseline_report.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "business_capability_baseline_report_guard.json"


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


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def main() -> int:
    policy = _load_json(BASELINE_JSON)
    if not policy:
        print("[business_capability_baseline_report_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[business_capability_baseline_report_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    errors: list[str] = []
    if not bool(report.get("ok")):
        errors.append("report.ok must be true")

    failed_check_count = _safe_int(summary.get("failed_check_count"), 0)
    error_count = _safe_int(summary.get("error_count"), 0)
    required_intent_count = _safe_int(summary.get("required_intent_count"), 0)
    required_role_count = _safe_int(summary.get("required_role_count"), 0)
    catalog_runtime_ratio = _safe_float(summary.get("catalog_runtime_ratio"), 0.0)

    if failed_check_count > _safe_int(policy.get("max_failed_check_count"), 0):
        errors.append(
            f"failed_check_count exceeded: {failed_check_count} > {policy.get('max_failed_check_count')}"
        )
    if error_count > _safe_int(policy.get("max_error_count"), 0):
        errors.append(f"error_count exceeded: {error_count} > {policy.get('max_error_count')}")
    if required_intent_count < _safe_int(policy.get("min_required_intent_count"), 0):
        errors.append(
            f"required_intent_count too small: {required_intent_count} < {policy.get('min_required_intent_count')}"
        )
    if required_role_count < _safe_int(policy.get("min_required_role_count"), 0):
        errors.append(
            f"required_role_count too small: {required_role_count} < {policy.get('min_required_role_count')}"
        )
    if catalog_runtime_ratio < _safe_float(policy.get("min_catalog_runtime_ratio"), 0.0):
        errors.append(
            f"catalog_runtime_ratio too small: {catalog_runtime_ratio} < {policy.get('min_catalog_runtime_ratio')}"
        )

    if errors:
        print("[business_capability_baseline_report_guard] FAIL")
        for item in errors:
            print(item)
        return 1
    print("[business_capability_baseline_report_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
