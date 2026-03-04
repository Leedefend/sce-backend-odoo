#!/usr/bin/env python3
"""Schema guard for grouped drift summary report artifact."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "grouped_drift_summary_guard.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "grouped_drift_summary_schema_guard.json"


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
        print("[grouped_drift_summary_schema_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    payload = _load_json(REPORT_JSON)
    if not payload:
        print("[grouped_drift_summary_schema_guard] FAIL")
        print(f"missing or invalid report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    errors: list[str] = []

    required_top_keys = baseline.get("required_top_keys") if isinstance(baseline.get("required_top_keys"), list) else []
    required_summary_keys = baseline.get("required_summary_keys") if isinstance(baseline.get("required_summary_keys"), list) else []

    for key in required_top_keys:
        key = str(key).strip()
        if key and key not in payload:
            errors.append(f"missing top-level key: {key}")

    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    for key in required_summary_keys:
        key = str(key).strip()
        if key and key not in summary:
            errors.append(f"missing summary key: {key}")

    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    if not isinstance(payload.get("errors"), list):
        errors.append("errors must be list")
    if not isinstance(payload.get("policy"), dict):
        errors.append("policy must be object")

    report = payload.get("report") if isinstance(payload.get("report"), dict) else {}
    if not str(report.get("json") or "").strip():
        errors.append("report.json must be non-empty")
    if not str(report.get("md") or "").strip():
        errors.append("report.md must be non-empty")

    if errors:
        print("[grouped_drift_summary_schema_guard] FAIL")
        for line in errors:
            print(line)
        return 1

    print("[grouped_drift_summary_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
