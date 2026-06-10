#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "docs" / "product" / "business_capability_productization_baseline_v1.json"
PORTRAIT_JSON = ROOT / "artifacts" / "user_business_data_portrait.sc_demo.json"
OUT_JSON = ROOT / "artifacts" / "user_business_productization_baseline_guard.json"
OUT_MD = ROOT / "artifacts" / "user_business_productization_baseline_guard.md"


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _family_portrait_index(portrait: dict) -> dict:
    result = {}
    for family in _as_list(portrait.get("families")):
        if not isinstance(family, dict):
            continue
        key = str(family.get("key") or "").strip()
        if key:
            result[key] = family
    return result


def main() -> int:
    baseline = _load_json(BASELINE_JSON)
    portrait = _load_json(PORTRAIT_JSON)
    errors: list[str] = []
    warnings: list[str] = []
    checks: list[dict] = []

    if not baseline:
        print("[user_business_productization_baseline_guard] FAIL")
        print(f"missing or invalid baseline: {BASELINE_JSON.relative_to(ROOT).as_posix()}")
        return 1
    if not portrait:
        print("[user_business_productization_baseline_guard] FAIL")
        print(f"missing or invalid portrait: {PORTRAIT_JSON.relative_to(ROOT).as_posix()}")
        return 1

    policy = baseline.get("policy") if isinstance(baseline.get("policy"), dict) else {}
    baseline_families = _as_list(baseline.get("families"))
    portrait_by_key = _family_portrait_index(portrait)
    required_family_count = _safe_int(policy.get("required_family_count"), 0)
    min_total_profiled_records = _safe_int(policy.get("min_total_profiled_records"), 0)
    total_profiled_records = _safe_int(
        (portrait.get("summary") if isinstance(portrait.get("summary"), dict) else {}).get("total_profiled_records"),
        0,
    )

    if len(baseline_families) != required_family_count:
        errors.append(f"baseline family count mismatch: {len(baseline_families)} != {required_family_count}")
    if len(portrait_by_key) < required_family_count:
        errors.append(f"portrait family count too small: {len(portrait_by_key)} < {required_family_count}")
    if total_profiled_records < min_total_profiled_records:
        errors.append(
            f"total_profiled_records too small: {total_profiled_records} < {min_total_profiled_records}"
        )

    for family in baseline_families:
        if not isinstance(family, dict):
            errors.append("baseline contains non-object family")
            continue
        key = str(family.get("key") or "").strip()
        name = str(family.get("name") or key)
        portrait_family = portrait_by_key.get(key)
        if not key:
            errors.append(f"{name}: missing key")
            continue
        if not portrait_family:
            errors.append(f"{name}: missing in portrait")
            checks.append({"key": key, "name": name, "ok": False, "reason": "missing_portrait"})
            continue

        assessment = (
            portrait_family.get("assessment")
            if isinstance(portrait_family.get("assessment"), dict)
            else {}
        )
        record_count = _safe_int(assessment.get("record_count"), 0)
        populated_model_count = _safe_int(assessment.get("populated_model_count"), 0)
        handling_model_count = _safe_int(assessment.get("handling_model_count"), 0)
        primary_models = _as_list(family.get("primary_models"))
        handling_entries = _as_list(family.get("handling_entries"))
        source_fact_entries = _as_list(family.get("source_fact_entries"))
        summary_entries = _as_list(family.get("summary_entries"))
        required_relationships = _as_list(family.get("required_relationships"))

        family_errors = []
        if policy.get("require_all_families_with_data") and record_count <= 0:
            family_errors.append("no profiled records")
        if populated_model_count <= 0:
            family_errors.append("no populated model")
        if not primary_models:
            family_errors.append("missing primary_models")
        if not handling_entries:
            family_errors.append("missing handling_entries")
        if not source_fact_entries and family.get("role") != "master_anchor":
            family_errors.append("missing source_fact_entries")
        if family.get("priority") in ("P0", "P1") and handling_model_count <= 0:
            family_errors.append("P0/P1 family has no handling-capable model")
        if family.get("priority") in ("P0", "P1") and not required_relationships and family.get("role") != "audit_evidence":
            family_errors.append("P0/P1 family missing required_relationships")
        if family.get("priority") == "P1" and not summary_entries and family.get("role") != "master_anchor":
            warnings.append(f"{name}: P1 family has no summary_entries")

        ok = not family_errors
        checks.append(
            {
                "key": key,
                "name": name,
                "priority": family.get("priority"),
                "ok": ok,
                "record_count": record_count,
                "populated_model_count": populated_model_count,
                "handling_model_count": handling_model_count,
                "primary_model_count": len(primary_models),
                "handling_entry_count": len(handling_entries),
                "source_fact_entry_count": len(source_fact_entries),
                "summary_entry_count": len(summary_entries),
                "errors": family_errors,
            }
        )
        errors.extend(f"{name}: {item}" for item in family_errors)

    report = {
        "ok": not errors,
        "baseline": BASELINE_JSON.relative_to(ROOT).as_posix(),
        "portrait": PORTRAIT_JSON.relative_to(ROOT).as_posix(),
        "summary": {
            "baseline_family_count": len(baseline_families),
            "portrait_family_count": len(portrait_by_key),
            "total_profiled_records": total_profiled_records,
            "check_count": len(checks),
            "failed_check_count": len([item for item in checks if not item.get("ok")]),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# User Business Productization Baseline Guard",
        "",
        f"- status: {'PASS' if report['ok'] else 'FAIL'}",
        f"- baseline_family_count: {report['summary']['baseline_family_count']}",
        f"- portrait_family_count: {report['summary']['portrait_family_count']}",
        f"- total_profiled_records: {report['summary']['total_profiled_records']}",
        f"- failed_check_count: {report['summary']['failed_check_count']}",
        f"- error_count: {report['summary']['error_count']}",
        f"- warning_count: {report['summary']['warning_count']}",
        "",
        "## Families",
        "",
    ]
    for item in checks:
        lines.append(
            f"- {item['name']}: {'PASS' if item['ok'] else 'FAIL'} "
            f"(records={item['record_count']}, handling_models={item['handling_model_count']})"
        )
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {item}" for item in errors)
    if warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in warnings)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(OUT_JSON.relative_to(ROOT)))
    print(str(OUT_MD.relative_to(ROOT)))
    if errors:
        print("[user_business_productization_baseline_guard] FAIL")
        return 1
    print("[user_business_productization_baseline_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
