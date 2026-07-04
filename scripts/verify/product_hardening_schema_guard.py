#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_JSON = ROOT / "artifacts" / "backend" / "bundle_installation_report.json"
BUNDLE_MD = ROOT / "docs" / "ops" / "audit" / "bundle_installation_report.md"
PERFORMANCE_JSON = ROOT / "artifacts" / "backend" / "platform_performance_smoke.json"
PERFORMANCE_MD = ROOT / "docs" / "ops" / "audit" / "platform_performance_smoke.md"
EXPECTED_BUNDLES = {"construction", "owner"}
EXPECTED_INTENTS = {"system.init", "ui.contract", "execute_button"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _require_summary(summary: object, keys: tuple[str, ...], errors: list[str]) -> dict:
    if not isinstance(summary, dict):
        errors.append("summary must be object")
        return {}
    for key in keys:
        if not isinstance(summary.get(key), int):
            errors.append(f"summary.{key} must be int")
    return summary


def _check_bundle_rows(bundles: object, errors: list[str]) -> dict:
    if not isinstance(bundles, dict):
        errors.append("bundles must be object")
        return {}
    seen = set(bundles)
    if seen != EXPECTED_BUNDLES:
        errors.append(f"bundles must cover {sorted(EXPECTED_BUNDLES)}")
    for name, row in bundles.items():
        prefix = f"bundles.{name}"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be object")
            continue
        for key in ("scene_count", "capability_count"):
            if not isinstance(row.get(key), int) or row.get(key) < 1:
                errors.append(f"{prefix}.{key} must be positive int")
        for key in (
            "enabled_shape_keys",
            "disabled_shape_keys",
            "enabled_extra_keys",
            "disabled_extra_keys",
            "missing_after_disabled",
        ):
            if not _string_list(row.get(key)):
                errors.append(f"{prefix}.{key} must be string list")
        unsupported_enabled_keys = set(row.get("enabled_extra_keys") or []) - {"ext_facts"}
        if unsupported_enabled_keys:
            errors.append(f"{prefix}.enabled_extra_keys must only contain ext_facts")
        if row.get("disabled_extra_keys"):
            errors.append(f"{prefix}.disabled_extra_keys must be empty")
        if row.get("missing_after_disabled"):
            errors.append(f"{prefix}.missing_after_disabled must be empty")
    return bundles


def _check_bundle() -> list[str]:
    payload = _load_json(BUNDLE_JSON)
    errors: list[str] = []
    if not payload:
        return [f"missing or invalid json: {BUNDLE_JSON.relative_to(ROOT).as_posix()}"]
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = _require_summary(payload.get("summary"), ("baseline_shape_count", "error_count", "warning_count"), errors)
    bundles = _check_bundle_rows(payload.get("bundles"), errors)
    report_errors = payload.get("errors")
    if not _string_list(report_errors):
        errors.append("errors must be string list")
        report_errors = []
    warnings = payload.get("warnings")
    if not _string_list(warnings):
        errors.append("warnings must be string list")
        warnings = []
    if summary:
        if summary.get("error_count") != len(report_errors):
            errors.append("summary.error_count must match errors length")
        if summary.get("warning_count") != len(warnings):
            errors.append("summary.warning_count must match warnings length")
        if len(bundles) == len(EXPECTED_BUNDLES) and summary.get("baseline_shape_count", 0) < 1:
            errors.append("summary.baseline_shape_count must be positive when bundles are present")
    if payload.get("ok") is True and report_errors:
        errors.append("ok=true report must not contain errors")
    if payload.get("ok") is False and not report_errors:
        errors.append("ok=false report must contain errors")
    if not BUNDLE_MD.is_file():
        errors.append(f"missing markdown report: {BUNDLE_MD.relative_to(ROOT).as_posix()}")
    else:
        text = BUNDLE_MD.read_text(encoding="utf-8")
        for token in ("# Bundle Installation Report", "- baseline_shape_count:", "## Bundles", "## Errors"):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")
    return errors


def _check_performance_row(row: object, idx: int, errors: list[str]) -> None:
    prefix = f"rows[{idx}]"
    if not isinstance(row, dict):
        errors.append(f"{prefix} must be object")
        return
    intent = str(row.get("intent") or "").strip()
    if intent not in EXPECTED_INTENTS:
        errors.append(f"{prefix}.intent must be one of {sorted(EXPECTED_INTENTS)}")
    for key in ("iterations", "max_payload_bytes", "threshold_payload_bytes"):
        if not isinstance(row.get(key), int) or row.get(key) < 1:
            errors.append(f"{prefix}.{key} must be positive int")
    for key in ("avg_ms", "p95_ms", "threshold_p95_ms"):
        if not isinstance(row.get(key), (int, float)) or row.get(key) < 0:
            errors.append(f"{prefix}.{key} must be non-negative number")
    status_codes = row.get("status_codes")
    if not isinstance(status_codes, list) or not status_codes or not all(isinstance(item, int) for item in status_codes):
        errors.append(f"{prefix}.status_codes must be non-empty int list")


def _check_performance() -> list[str]:
    payload = _load_json(PERFORMANCE_JSON)
    errors: list[str] = []
    if not payload:
        return [f"missing or invalid json: {PERFORMANCE_JSON.relative_to(ROOT).as_posix()}"]
    if not isinstance(payload.get("ok"), bool):
        errors.append("ok must be bool")
    summary = _require_summary(payload.get("summary"), ("target_count", "iterations", "error_count", "warning_count"), errors)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        errors.append("rows must be list")
        rows = []
    seen_intents: set[str] = set()
    for idx, row in enumerate(rows):
        _check_performance_row(row, idx, errors)
        if isinstance(row, dict):
            seen_intents.add(str(row.get("intent") or "").strip())
    if seen_intents != EXPECTED_INTENTS:
        errors.append(f"rows must cover {sorted(EXPECTED_INTENTS)}")
    report_errors = payload.get("errors")
    if not _string_list(report_errors):
        errors.append("errors must be string list")
        report_errors = []
    warnings = payload.get("warnings")
    if not _string_list(warnings):
        errors.append("warnings must be string list")
        warnings = []
    if summary:
        if summary.get("target_count") != len(rows):
            errors.append("summary.target_count must match rows length")
        if summary.get("error_count") != len(report_errors):
            errors.append("summary.error_count must match errors length")
        if summary.get("warning_count") != len(warnings):
            errors.append("summary.warning_count must match warnings length")
        for idx, row in enumerate(rows):
            if isinstance(row, dict) and row.get("iterations") != summary.get("iterations"):
                errors.append(f"rows[{idx}].iterations must match summary.iterations")
    if payload.get("ok") is True and report_errors:
        errors.append("ok=true report must not contain errors")
    if payload.get("ok") is False and not report_errors:
        errors.append("ok=false report must contain errors")
    if not PERFORMANCE_MD.is_file():
        errors.append(f"missing markdown report: {PERFORMANCE_MD.relative_to(ROOT).as_posix()}")
    else:
        text = PERFORMANCE_MD.read_text(encoding="utf-8")
        for token in ("# Platform Performance Smoke", "- target_count:", "| intent | avg_ms |", "## Errors"):
            if token not in text:
                errors.append(f"markdown report missing token: {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate product hardening report schemas")
    parser.add_argument("--report", choices=("bundle", "performance", "all"), default="all")
    args = parser.parse_args()

    errors: list[str] = []
    if args.report in {"bundle", "all"}:
        errors.extend(f"bundle: {error}" for error in _check_bundle())
    if args.report in {"performance", "all"}:
        errors.extend(f"performance: {error}" for error in _check_performance())

    if errors:
        print("[product_hardening_schema_guard] FAIL")
        for error in errors:
            print(error)
        return 2
    print("[product_hardening_schema_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
