#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
REPORT_JSON = ROOT / "artifacts" / "backend" / "system_capability_baseline_report.json"
REPORT_MD = ROOT / "artifacts" / "backend" / "system_capability_baseline_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_json(REPORT_JSON)
    errors: list[str] = []

    if not payload:
        errors.append(f"missing or invalid json: {REPORT_JSON.relative_to(ROOT).as_posix()}")
    else:
        if not isinstance(payload.get("ok"), bool):
            errors.append("ok must be bool")
        for key in ("version", "scope"):
            if not isinstance(payload.get(key), str) or not payload.get(key):
                errors.append(f"{key} must be non-empty string")

        summary = payload.get("summary")
        if not isinstance(summary, dict):
            errors.append("summary must be object")
            summary = {}
        for key in (
            "check_count",
            "failed_check_count",
            "module_count",
            "delivery_scope_scene_count",
            "business_required_intent_count",
            "business_required_role_count",
        ):
            if not isinstance(summary.get(key), int):
                errors.append(f"summary.{key} must be int")

        checks = payload.get("checks")
        if not isinstance(checks, list):
            errors.append("checks must be list")
            checks = []
        names: list[str] = []
        failed_count = 0
        for idx, row in enumerate(checks):
            if not isinstance(row, dict):
                errors.append(f"checks[{idx}] must be object")
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                errors.append(f"checks[{idx}].name must be non-empty string")
            names.append(name)
            if not isinstance(row.get("ok"), bool):
                errors.append(f"checks[{idx}].ok must be bool")
            if row.get("ok") is not True:
                failed_count += 1
            if name.startswith("metric:") and not isinstance(row.get("observed"), int):
                errors.append(f"checks[{idx}].observed must be int for metric checks")
        if names != sorted(names):
            errors.append("checks must be sorted by name")
        if isinstance(summary.get("check_count"), int) and summary["check_count"] != len(checks):
            errors.append("summary.check_count must match checks length")
        if isinstance(summary.get("failed_check_count"), int) and summary["failed_check_count"] != failed_count:
            errors.append("summary.failed_check_count must match failed checks length")

        report_errors = payload.get("errors")
        if not isinstance(report_errors, list) or not all(isinstance(item, str) for item in report_errors):
            errors.append("errors must be string list")
            report_errors = []
        if payload.get("ok") is True and report_errors:
            errors.append("ok=true report must not contain errors")
        if payload.get("ok") is False and not report_errors:
            errors.append("ok=false report must contain errors")

        baseline = payload.get("baseline")
        if not isinstance(baseline, dict):
            errors.append("baseline must be object")
        else:
            for key in ("version", "scope", "minimum_acceptance", "required_docs", "required_make_targets"):
                if key not in baseline:
                    errors.append(f"baseline missing key: {key}")

    if not REPORT_MD.is_file():
        errors.append(f"missing markdown report: {REPORT_MD.relative_to(ROOT).as_posix()}")
    else:
        text = REPORT_MD.read_text(encoding="utf-8")
        for token in (
            "# System Capability Baseline Report",
            "- status:",
            "- check_count:",
            "- failed_check_count:",
            "## Checks",
        ):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")

    if errors:
        print("[system_capability_baseline_report_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2

    print("[system_capability_baseline_report_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
