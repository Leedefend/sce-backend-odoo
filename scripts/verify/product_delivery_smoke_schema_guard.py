#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
ACTION_JSON = ROOT / "artifacts" / "backend" / "product_delivery_action_closure_report.json"
ACTION_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_action_closure_report.md"
MODULE_JSON = ROOT / "artifacts" / "backend" / "product_delivery_module9_smoke_report.json"
MODULE_MD = ROOT / "docs" / "ops" / "audit" / "product_delivery_module9_smoke_report.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _require_summary(summary: object, keys: tuple[str, ...], errors: list[str]) -> dict:
    if not isinstance(summary, dict):
        errors.append("summary must be object")
        return {}
    for key in keys:
        if not isinstance(summary.get(key), int):
            errors.append(f"summary.{key} must be int")
    return summary


def _check_action() -> list[str]:
    payload = _load_json(ACTION_JSON)
    errors: list[str] = []
    if not payload:
        return [f"missing or invalid json: {ACTION_JSON.relative_to(ROOT).as_posix()}"]
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = _require_summary(payload.get("summary"), ("target_count", "pass_count", "failed_count", "error_count"), errors)
    checks = payload.get("checks")
    if not isinstance(checks, list):
        errors.append("checks must be list")
        checks = []
    for idx, row in enumerate(checks):
        if not isinstance(row, dict):
            errors.append(f"checks[{idx}] must be object")
            continue
        for key in ("scene_key", "label"):
            if not isinstance(row.get(key), str) or not row.get(key):
                errors.append(f"checks[{idx}].{key} must be non-empty string")
        if not isinstance(row.get("ok"), bool):
            errors.append(f"checks[{idx}].ok must be bool")
        issues = row.get("issues")
        if not isinstance(issues, list) or not all(isinstance(item, str) for item in issues):
            errors.append(f"checks[{idx}].issues must be string list")
    report_errors = payload.get("errors")
    if not isinstance(report_errors, list) or not all(isinstance(item, str) for item in report_errors):
        errors.append("errors must be string list")
        report_errors = []
    if summary:
        failed_count = len([row for row in checks if isinstance(row, dict) and row.get("ok") is not True])
        if summary.get("target_count") != len(checks):
            errors.append("summary.target_count must match checks length")
        if summary.get("failed_count") != failed_count:
            errors.append("summary.failed_count must match failed checks length")
        if summary.get("pass_count") != len(checks) - failed_count:
            errors.append("summary.pass_count must match passed checks length")
        if summary.get("error_count") != len(report_errors):
            errors.append("summary.error_count must match errors length")
    if payload.get("ok") is True and report_errors:
        errors.append("ok=true report must not contain errors")
    if not ACTION_MD.is_file():
        errors.append(f"missing markdown report: {ACTION_MD.relative_to(ROOT).as_posix()}")
    else:
        text = ACTION_MD.read_text(encoding="utf-8")
        for token in ("# Product Delivery Action Closure Smoke", "- target_count:", "## Checks"):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")
    return errors


def _check_module() -> list[str]:
    payload = _load_json(MODULE_JSON)
    errors: list[str] = []
    if not payload:
        return [f"missing or invalid json: {MODULE_JSON.relative_to(ROOT).as_posix()}"]
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = _require_summary(
        payload.get("summary"),
        ("module_count", "pass_count", "failed_count", "runtime_ready_count", "runtime_pending_count", "error_count"),
        errors,
    )
    checks = payload.get("checks")
    if not isinstance(checks, list):
        errors.append("checks must be list")
        checks = []
    for idx, row in enumerate(checks):
        if not isinstance(row, dict):
            errors.append(f"checks[{idx}] must be object")
            continue
        for key in ("module_key", "module_name"):
            if not isinstance(row.get(key), str) or not row.get(key):
                errors.append(f"checks[{idx}].{key} must be non-empty string")
        for key in ("entry_scene_count", "present_count", "missing_count", "runtime_missing_count"):
            if not isinstance(row.get(key), int):
                errors.append(f"checks[{idx}].{key} must be int")
        for key in ("missing_scenes", "runtime_missing_scenes", "missing_out_of_scope_scenes"):
            value = row.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"checks[{idx}].{key} must be string list")
        if not isinstance(row.get("resolved_entry_scenes"), dict):
            errors.append(f"checks[{idx}].resolved_entry_scenes must be object")
        for key in ("runtime_ready", "ok"):
            if not isinstance(row.get(key), bool):
                errors.append(f"checks[{idx}].{key} must be bool")
    report_errors = payload.get("errors")
    if not isinstance(report_errors, list) or not all(isinstance(item, str) for item in report_errors):
        errors.append("errors must be string list")
        report_errors = []
    if summary:
        failed_count = len([row for row in checks if isinstance(row, dict) and row.get("ok") is not True])
        runtime_ready_count = len([row for row in checks if isinstance(row, dict) and row.get("runtime_ready") is True])
        if summary.get("module_count") != len(checks):
            errors.append("summary.module_count must match checks length")
        if summary.get("failed_count") != failed_count:
            errors.append("summary.failed_count must match failed checks length")
        if summary.get("pass_count") != len(checks) - failed_count:
            errors.append("summary.pass_count must match passed checks length")
        if summary.get("runtime_ready_count") != runtime_ready_count:
            errors.append("summary.runtime_ready_count must match ready checks length")
        if summary.get("runtime_pending_count") != len(checks) - runtime_ready_count:
            errors.append("summary.runtime_pending_count must match pending checks length")
        if summary.get("error_count") != len(report_errors):
            errors.append("summary.error_count must match errors length")
    if payload.get("ok") is True and report_errors:
        errors.append("ok=true report must not contain errors")
    if not MODULE_MD.is_file():
        errors.append(f"missing markdown report: {MODULE_MD.relative_to(ROOT).as_posix()}")
    else:
        text = MODULE_MD.read_text(encoding="utf-8")
        for token in ("# Product Delivery Module Capability Smoke", "- module_count:", "| module | status | runtime_status |"):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate product delivery smoke report schemas")
    parser.add_argument("--report", choices=("action", "module", "all"), default="all")
    args = parser.parse_args()

    errors: list[str] = []
    if args.report in {"action", "all"}:
        errors.extend(f"action: {error}" for error in _check_action())
    if args.report in {"module", "all"}:
        errors.extend(f"module: {error}" for error in _check_module())

    if errors:
        print("[product_delivery_smoke_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[product_delivery_smoke_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
