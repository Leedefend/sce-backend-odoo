#!/usr/bin/env python3
"""Schema guard for grouped governance brief artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_governance_brief_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_governance_brief_schema_guard.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _to_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[grouped_governance_brief_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    payload = _load_json(REPORT_JSON)
    if not payload:
        print("[grouped_governance_brief_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []
    required_top_keys = _to_str_list(baseline.get("required_top_keys"))
    required_summary_keys = _to_str_list(baseline.get("required_summary_keys"))
    required_check_keys = _to_str_list(baseline.get("required_check_keys"))
    required_trend_delta_keys = _to_str_list(baseline.get("required_trend_delta_keys"))

    for key in required_top_keys:
        if key not in payload:
            errors.append(f"missing top-level key: {key}")

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    for key in required_summary_keys:
        if key not in summary:
            errors.append(f"missing summary key: {key}")

    checks = payload.get("checks") if isinstance(payload.get("checks"), dict) else {}
    for key in required_check_keys:
        if key not in checks:
            errors.append(f"missing checks key: {key}")

    trend = payload.get("trend") if isinstance(payload.get("trend"), dict) else {}
    delta = trend.get("delta") if isinstance(trend.get("delta"), dict) else {}
    for key in required_trend_delta_keys:
        if key not in delta:
            errors.append(f"missing trend.delta key: {key}")

    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    if not isinstance(payload.get("issues"), list):
        errors.append("issues must be list")
    if not isinstance(payload.get("inputs"), dict):
        errors.append("inputs must be object")
    if not isinstance(payload.get("generated_at"), str) or not payload.get("generated_at"):
        errors.append("generated_at must be non-empty string")
    if not isinstance(trend.get("has_previous"), bool):
        errors.append("trend.has_previous must be bool")

    if errors:
        print("[grouped_governance_brief_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_governance_brief_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
