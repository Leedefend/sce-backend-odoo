#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_JSON = ROOT / "docs" / "ops" / "stress_regression_policy_v1.json"
REPORT_JSON = ROOT / "artifacts" / "backend" / "stress_regression_policy_guard_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "stress_regression_policy_guard_report.md"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _num(v: object, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    policy = _load(POLICY_JSON)
    if not policy:
        errors.append("missing stress policy file")

    rel = policy.get("relative_thresholds") if isinstance(policy.get("relative_thresholds"), dict) else {}
    warn_factor = _num(rel.get("warn_factor"), -1.0)
    fail_factor = _num(rel.get("fail_factor"), -1.0)
    if not (1.0 <= warn_factor <= fail_factor):
        errors.append("relative thresholds invalid: require 1.0 <= warn <= fail")

    abs_all = policy.get("absolute_thresholds_ms") if isinstance(policy.get("absolute_thresholds_ms"), dict) else {}
    default_abs = abs_all.get("default") if isinstance(abs_all.get("default"), dict) else {}
    default_warn = _num(default_abs.get("warn"), -1)
    default_fail = _num(default_abs.get("fail"), -1)
    if default_warn < 0 or default_fail < default_warn:
        errors.append("default absolute thresholds invalid")

    floor = policy.get("absolute_floor_ms") if isinstance(policy.get("absolute_floor_ms"), dict) else {}
    floor_exec = floor.get("execute_button") if isinstance(floor.get("execute_button"), dict) else {}
    floor_warn = _num(floor_exec.get("warn"), 0)
    floor_fail = _num(floor_exec.get("fail"), 0)
    if floor_fail < floor_warn:
        errors.append("execute_button floor thresholds invalid")

    for intent in ("system.init", "ui.contract", "execute_button"):
        row = abs_all.get(intent) if isinstance(abs_all.get(intent), dict) else {}
        warn = _num(row.get("warn"), -1)
        fail = _num(row.get("fail"), -1)
        if warn < 0 or fail < warn:
            errors.append(f"{intent} absolute thresholds invalid")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "policy_version": str(policy.get("version") or "unknown"),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Stress Regression Policy Guard",
        "",
        f"- policy_version: {payload['summary']['policy_version']}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
    ]
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[stress_regression_policy_guard] FAIL")
        return 2
    print("[stress_regression_policy_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
