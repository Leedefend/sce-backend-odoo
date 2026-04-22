#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
ARTIFACTS_DIR = ROOT / "artifacts" / "backend"
SUITE_PATH = ROOT / "scripts" / "verify" / "scene_governance_suite.py"
OUT_JSON = ARTIFACTS_DIR / "scene_governance_guard_export_parity_guard.json"
OUT_MD = ARTIFACTS_DIR / "scene_governance_guard_export_parity_guard.md"

AUTHORITY_CSV = GENERATED_DIR / "scene_authority_matrix_current_v1.csv"
PROVIDER_CSV = GENERATED_DIR / "provider_completeness_current_v1.csv"

AUTHORITY_GUARD_JSON = ARTIFACTS_DIR / "backend_scene_authority_guard.json"
PROVIDER_GUARD_JSON = ARTIFACTS_DIR / "backend_scene_provider_completeness_guard.json"
EXPORT_CONSISTENCY_GUARD_JSON = ARTIFACTS_DIR / "scene_governance_export_consistency_guard.json"

REQUIRED_SUITE_COMMANDS = {
    "scripts/verify/backend_scene_authority_guard.py",
    "scripts/verify/backend_scene_provider_completeness_guard.py",
    "scripts/verify/scene_governance_export_consistency_guard.py",
    "scripts/verify/scene_governance_baseline_drift_guard.py",
}


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean(value: object) -> str:
    return str(value or "").strip()


def _load_suite_commands() -> list[str]:
    tree = ast.parse(SUITE_PATH.read_text(encoding="utf-8"), filename=SUITE_PATH.as_posix())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "COMMANDS":
                    value = ast.literal_eval(node.value)
                    return [str(item[1]) for item in value if isinstance(item, list) and len(item) >= 2]
    raise RuntimeError("COMMANDS not found in scene_governance_suite.py")


def _build_report() -> tuple[dict[str, object], list[str]]:
    errors: list[str] = []

    authority_rows = _read_csv(AUTHORITY_CSV)
    provider_rows = _read_csv(PROVIDER_CSV)

    authority_guard = _read_json(AUTHORITY_GUARD_JSON)
    provider_guard = _read_json(PROVIDER_GUARD_JSON)
    export_consistency_guard = _read_json(EXPORT_CONSISTENCY_GUARD_JSON)
    suite_commands = _load_suite_commands()

    authority_scene_codes = [
        _clean(row.get("scene_key"))
        for row in authority_rows
        if _clean(row.get("scene_key"))
    ]
    guarded_scene_codes = [
        _clean(row.get("code"))
        for row in authority_guard.get("scenes", [])
        if isinstance(row, dict) and _clean(row.get("code"))
    ]
    baseline_scene_count = int(authority_guard.get("baseline_scene_count", 0))
    if len(guarded_scene_codes) != baseline_scene_count:
        errors.append(
            f"authority parity: baseline_scene_count={baseline_scene_count} but guarded scenes={len(guarded_scene_codes)}"
        )
    missing_authority_codes = [code for code in guarded_scene_codes if code not in authority_scene_codes]
    if missing_authority_codes:
        errors.append(
            f"authority parity: missing guarded scene codes in export: {missing_authority_codes}"
        )

    provider_checked_scene_count = int(provider_guard.get("checked_scene_count", 0))
    if provider_checked_scene_count != len(provider_rows):
        errors.append(
            f"provider parity: checked_scene_count={provider_checked_scene_count} export_rows={len(provider_rows)}"
        )
    computed_incomplete = [
        _clean(row.get("scene_key"))
        for row in provider_rows
        if _clean(row.get("provider_registered")).lower() != "true"
        and _clean(row.get("explicit_fallback_present")).lower() != "true"
        and _clean(row.get("scene_key"))
    ]
    guard_incomplete = [
        _clean(item)
        for item in provider_guard.get("incomplete_scenes", [])
        if _clean(item)
    ]
    if computed_incomplete != guard_incomplete:
        errors.append(
            f"provider parity: incomplete_scenes guard={guard_incomplete} export={computed_incomplete}"
        )

    asset_reports = export_consistency_guard.get("asset_reports", [])
    asset_names = [
        _clean(item.get("name"))
        for item in asset_reports
        if isinstance(item, dict) and _clean(item.get("name"))
    ]
    expected_asset_names = [
        "authority",
        "family_inventory",
        "menu_mapping",
        "provider_completeness",
        "high_priority_family_closure",
    ]
    if asset_names != expected_asset_names:
        errors.append(
            f"export-consistency parity: asset_reports guard={asset_names} expected={expected_asset_names}"
        )

    missing_suite_commands = sorted(REQUIRED_SUITE_COMMANDS.difference(suite_commands))
    if missing_suite_commands:
        errors.append(
            f"suite parity: missing required guard commands {missing_suite_commands}"
        )

    report = {
        "status": "PASS" if not errors else "FAIL",
        "parity_relations": [
            "authority_guard_vs_authority_export",
            "provider_guard_vs_provider_export",
            "export_consistency_guard_vs_governed_asset_pairs",
            "suite_command_set_vs_required_governance_guards",
        ],
        "authority_parity": {
            "baseline_scene_count": baseline_scene_count,
            "guarded_scene_count": len(guarded_scene_codes),
            "missing_scene_codes_in_export": missing_authority_codes,
        },
        "provider_parity": {
            "checked_scene_count": provider_checked_scene_count,
            "export_row_count": len(provider_rows),
            "guard_incomplete_scenes": guard_incomplete,
            "computed_incomplete_scenes": computed_incomplete,
        },
        "export_consistency_parity": {
            "asset_report_names": asset_names,
            "expected_asset_report_names": expected_asset_names,
        },
        "suite_parity": {
            "suite_commands": suite_commands,
            "required_commands": sorted(REQUIRED_SUITE_COMMANDS),
            "missing_required_commands": missing_suite_commands,
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
        "# Scene Governance Guard Export Parity Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- parity_relations: {'|'.join(report.get('parity_relations', []))}",
    ]
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend([f"- {item}" for item in errors])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[scene_governance_guard_export_parity_guard] FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("[scene_governance_guard_export_parity_guard] PASS")
    print("parity_relations=4")
    return 0


if __name__ == "__main__":
    sys.exit(main())
