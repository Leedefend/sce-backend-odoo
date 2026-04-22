#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
BASELINE_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets"
OUT_JSON = ROOT / "artifacts" / "backend" / "scene_governance_baseline_drift_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "scene_governance_baseline_drift_guard.md"

ASSET_SPECS = [
    {
        "name": "authority",
        "current": GENERATED_DIR / "scene_authority_matrix_current_v1.csv",
        "baseline": BASELINE_DIR / "scene_authority_matrix_baseline_v1.csv",
        "key_field": "scene_key",
    },
    {
        "name": "family_inventory",
        "current": GENERATED_DIR / "scene_family_inventory_current_v1.csv",
        "baseline": BASELINE_DIR / "scene_family_inventory_baseline_v1.csv",
        "key_field": "family",
    },
    {
        "name": "menu_mapping",
        "current": GENERATED_DIR / "menu_scene_mapping_current_v1.csv",
        "baseline": BASELINE_DIR / "menu_scene_mapping_baseline_v1.csv",
        "key_field": "menu_xmlid",
    },
    {
        "name": "provider_completeness",
        "current": GENERATED_DIR / "provider_completeness_current_v1.csv",
        "baseline": BASELINE_DIR / "provider_completeness_baseline_v1.csv",
        "key_field": "scene_key",
    },
    {
        "name": "high_priority_family_closure",
        "current": GENERATED_DIR / "high_priority_family_user_flow_closure_current_v1.csv",
        "baseline": BASELINE_DIR / "high_priority_family_user_flow_closure_baseline_v1.csv",
        "key_field": "family",
    },
]


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _clean(value: object) -> str:
    return str(value or "").strip()


def _keys(rows: list[dict[str, str]], key_field: str) -> list[str]:
    return [_clean(row.get(key_field)) for row in rows]


def _build_report() -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    asset_reports: list[dict[str, object]] = []
    governed_ready_current: list[str] = []
    governed_ready_baseline: list[str] = []

    for spec in ASSET_SPECS:
        current_fields, current_rows = _read_csv(spec["current"])
        baseline_fields, baseline_rows = _read_csv(spec["baseline"])
        current_keys = _keys(current_rows, spec["key_field"])
        baseline_keys = _keys(baseline_rows, spec["key_field"])

        field_drift = current_fields != baseline_fields
        row_count_drift = len(current_rows) != len(baseline_rows)
        key_drift = current_keys != baseline_keys

        if field_drift:
            errors.append(
                f"{spec['name']}: schema drift baseline={baseline_fields} current={current_fields}"
            )
        if row_count_drift:
            errors.append(
                f"{spec['name']}: row-count drift baseline={len(baseline_rows)} current={len(current_rows)}"
            )
        if key_drift:
            errors.append(
                f"{spec['name']}: key-set drift baseline={baseline_keys} current={current_keys}"
            )

        if spec["name"] == "high_priority_family_closure":
            governed_ready_current = [
                _clean(row.get("family"))
                for row in current_rows
                if _clean(row.get("acceptance_status")) == "guarded_ready"
            ]
            governed_ready_baseline = [
                _clean(row.get("family"))
                for row in baseline_rows
                if _clean(row.get("acceptance_status")) == "guarded_ready"
            ]

        asset_reports.append(
            {
                "name": spec["name"],
                "current_csv": spec["current"].relative_to(ROOT).as_posix(),
                "baseline_csv": spec["baseline"].relative_to(ROOT).as_posix(),
                "key_field": spec["key_field"],
                "field_drift": field_drift,
                "row_count_drift": row_count_drift,
                "key_drift": key_drift,
                "baseline_row_count": len(baseline_rows),
                "current_row_count": len(current_rows),
            }
        )

    governed_ready_drift = governed_ready_current != governed_ready_baseline
    if governed_ready_drift:
        errors.append(
            "high_priority_family_closure: governed-ready family-set drift "
            f"baseline={governed_ready_baseline} current={governed_ready_current}"
        )

    report = {
        "status": "PASS" if not errors else "FAIL",
        "drift_surface": [
            "row-count",
            "key-set",
            "schema",
            "governed-ready-family-set",
        ],
        "asset_reports": asset_reports,
        "governed_ready_family_set": {
            "baseline": governed_ready_baseline,
            "current": governed_ready_current,
            "drift": governed_ready_drift,
        },
        "errors": errors,
    }
    return report, errors


def main() -> int:
    try:
        report, errors = _build_report()
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = list(report["errors"])

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")

    lines = [
        "# Scene Governance Baseline Drift Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- drift_surface: {'|'.join(report.get('drift_surface', []))}",
    ]
    family_set = report.get("governed_ready_family_set", {})
    if isinstance(family_set, dict):
        lines.extend(
            [
                f"- governed_ready_baseline: {'|'.join(family_set.get('baseline', []))}",
                f"- governed_ready_current: {'|'.join(family_set.get('current', []))}",
                f"- governed_ready_drift: {str(family_set.get('drift', False)).lower()}",
            ]
        )
    for asset_report in report.get("asset_reports", []):
        lines.extend(
            [
                "",
                f"## {asset_report['name']}",
                f"- baseline_row_count: {asset_report['baseline_row_count']}",
                f"- current_row_count: {asset_report['current_row_count']}",
                f"- field_drift: {str(asset_report['field_drift']).lower()}",
                f"- row_count_drift: {str(asset_report['row_count_drift']).lower()}",
                f"- key_drift: {str(asset_report['key_drift']).lower()}",
            ]
        )
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])

    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[scene_governance_baseline_drift_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_governance_baseline_drift_guard] PASS")
    print(
        "governed_ready_family_count="
        f"{len(report.get('governed_ready_family_set', {}).get('current', []))}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
