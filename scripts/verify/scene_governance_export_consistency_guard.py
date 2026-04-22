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
OUT_JSON = ROOT / "artifacts" / "backend" / "scene_governance_export_consistency_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "scene_governance_export_consistency_guard.md"

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


def _asset_key(row: dict[str, str], field: str) -> str:
    return _clean(row.get(field))


def _build_report() -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []
    asset_reports: list[dict[str, object]] = []
    current_rows_by_name: dict[str, list[dict[str, str]]] = {}

    for spec in ASSET_SPECS:
        current_fields, current_rows = _read_csv(spec["current"])
        baseline_fields, baseline_rows = _read_csv(spec["baseline"])
        current_rows_by_name[spec["name"]] = current_rows

        current_keys = [_asset_key(row, spec["key_field"]) for row in current_rows]
        baseline_keys = [_asset_key(row, spec["key_field"]) for row in baseline_rows]

        if current_fields != baseline_fields:
            errors.append(
                f"{spec['name']}: field mismatch baseline={baseline_fields} current={current_fields}"
            )
        if len(current_rows) != len(baseline_rows):
            errors.append(
                f"{spec['name']}: row count drift baseline={len(baseline_rows)} current={len(current_rows)}"
            )
        if current_keys != baseline_keys:
            errors.append(
                f"{spec['name']}: key drift baseline={baseline_keys} current={current_keys}"
            )

        asset_reports.append(
            {
                "name": spec["name"],
                "current_csv": spec["current"].relative_to(ROOT).as_posix(),
                "baseline_csv": spec["baseline"].relative_to(ROOT).as_posix(),
                "key_field": spec["key_field"],
                "fieldnames": current_fields,
                "current_row_count": len(current_rows),
                "baseline_row_count": len(baseline_rows),
                "current_keys": current_keys,
                "baseline_keys": baseline_keys,
            }
        )

    authority_rows = current_rows_by_name["authority"]
    family_rows = current_rows_by_name["family_inventory"]
    menu_rows = current_rows_by_name["menu_mapping"]
    provider_rows = current_rows_by_name["provider_completeness"]
    closure_rows = current_rows_by_name["high_priority_family_closure"]

    authority_by_scene = {_clean(row.get("scene_key")): row for row in authority_rows if _clean(row.get("scene_key"))}
    provider_by_scene = {_clean(row.get("scene_key")): row for row in provider_rows if _clean(row.get("scene_key"))}

    governed_families = {_clean(row.get("family")) for row in family_rows if _clean(row.get("family"))}
    family_provider_counts: dict[str, int] = {}
    for provider_row in provider_rows:
        scene_key = _clean(provider_row.get("scene_key"))
        provider_registered = _clean(provider_row.get("provider_registered")).lower() == "true"
        if not scene_key or not provider_registered:
            continue
        authority_row = authority_by_scene.get(scene_key)
        family = _clean(authority_row.get("family")) if authority_row else ""
        if not family or family not in governed_families:
            continue
        family_provider_counts[family] = family_provider_counts.get(family, 0) + 1

    for scene_key, authority_row in sorted(authority_by_scene.items()):
        provider_owner = _clean(authority_row.get("provider_owner"))
        if not provider_owner or provider_owner == "provider_tbd":
            continue
        provider_row = provider_by_scene.get(scene_key)
        if provider_row is None:
            errors.append(f"authority-provider: missing provider row for {scene_key}")
            continue
        provider_key = _clean(provider_row.get("provider_key"))
        provider_registered = _clean(provider_row.get("provider_registered")).lower() == "true"
        fallback_present = _clean(provider_row.get("explicit_fallback_present")).lower() == "true"
        if provider_key != provider_owner:
            errors.append(
                f"authority-provider: provider key mismatch for {scene_key}: authority={provider_owner} provider={provider_key or '(missing)'}"
            )
        if not provider_registered and not fallback_present:
            errors.append(
                f"authority-provider: {scene_key} lost provider registration without explicit fallback"
            )

    family_index = {_clean(row.get("family")): row for row in family_rows if _clean(row.get("family"))}
    for family, family_row in sorted(family_index.items()):
        declared_provider_count = _clean(family_row.get("provider_count"))
        actual_provider_count = str(family_provider_counts.get(family, 0))
        if declared_provider_count != actual_provider_count:
            errors.append(
                f"family-provider_count: {family} declared={declared_provider_count or '(missing)'} actual={actual_provider_count}"
            )

    for row in closure_rows:
        family = _clean(row.get("family"))
        acceptance_status = _clean(row.get("acceptance_status"))
        if acceptance_status != "guarded_ready":
            continue
        family_row = family_index.get(family)
        if family_row is None:
            errors.append(f"family-closure: missing family inventory row for {family}")
            continue
        verify_status = _clean(family_row.get("verify_status"))
        governance_status = _clean(family_row.get("governance_status"))
        if verify_status != "guarded" or governance_status != "stage_closed":
            errors.append(
                f"family-closure: {family} guarded_ready requires verify_status=guarded and governance_status=stage_closed, got {verify_status}/{governance_status}"
            )

    for row in menu_rows:
        menu_xmlid = _clean(row.get("menu_xmlid"))
        scene_key = _clean(row.get("resolved_scene_key"))
        if not menu_xmlid or not scene_key:
            continue
        if scene_key not in authority_by_scene:
            continue
        family = _clean(authority_by_scene[scene_key].get("family"))
        if family not in governed_families:
            errors.append(
                f"menu-authority: {menu_xmlid} resolves to non-governed authority scene {scene_key}"
            )

    governed_ready_families = [
        _clean(row.get("family"))
        for row in closure_rows
        if _clean(row.get("acceptance_status")) == "guarded_ready"
    ]

    report = {
        "status": "PASS" if not errors else "FAIL",
        "asset_reports": asset_reports,
        "consistency_relations": [
            "authority-provider",
            "family-provider_count",
            "family-closure",
            "menu-authority",
            "drift-candidate",
        ],
        "governed_ready_families": governed_ready_families,
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
        "# Scene Governance Export Consistency Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- governed_ready_family_count: {len(report.get('governed_ready_families', []))}",
        f"- consistency_relations: {'|'.join(report.get('consistency_relations', []))}",
    ]
    for asset_report in report.get("asset_reports", []):
        lines.extend(
            [
                "",
                f"## {asset_report['name']}",
                f"- current_csv: {asset_report['current_csv']}",
                f"- baseline_csv: {asset_report['baseline_csv']}",
                f"- key_field: {asset_report['key_field']}",
                f"- current_row_count: {asset_report['current_row_count']}",
                f"- baseline_row_count: {asset_report['baseline_row_count']}",
            ]
        )
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])

    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[scene_governance_export_consistency_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_governance_export_consistency_guard] PASS")
    print(f"governed_ready_family_count={len(report.get('governed_ready_families', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
