#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "controller_boundary_guard_report.json"
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "controller_boundary_guard_baseline.json"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    if not baseline:
        print("[controller_boundary_baseline_guard] FAIL")
        print(f"invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1

    report = _load_json(REPORT_JSON)
    if not report:
        print("[controller_boundary_baseline_guard] FAIL")
        print(f"missing report: {REPORT_JSON.relative_to(ROOT).as_posix()}")
        print("hint: run make verify.controller.boundary.report first")
        return 1

    baseline_checks = baseline.get("checks") if isinstance(baseline.get("checks"), dict) else {}
    max_errors = int(baseline.get("max_errors") or 0)
    checks = report.get("checks") if isinstance(report.get("checks"), list) else []

    errors: list[str] = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        actual = int(item.get("violation_count") or 0)
        conf = baseline_checks.get(name) if isinstance(baseline_checks.get(name), dict) else {}
        allowed = int(conf.get("max_violation_count") or 0)
        if actual > allowed:
            errors.append(
                f"{name}: violation_count {actual} > baseline max_violation_count {allowed}"
            )

    if len(errors) > max_errors:
        print("[controller_boundary_baseline_guard] FAIL")
        for item in errors:
            print(item)
        return 1

    print("[controller_boundary_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
