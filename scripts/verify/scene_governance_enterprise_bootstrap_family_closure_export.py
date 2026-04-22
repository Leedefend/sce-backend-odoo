#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
AUTHORITY_CSV = GEN_DIR / "scene_authority_matrix_current_v1.csv"
FAMILY_CSV = GEN_DIR / "scene_family_inventory_current_v1.csv"
MENU_CSV = GEN_DIR / "menu_scene_mapping_current_v1.csv"
PROVIDER_CSV = GEN_DIR / "provider_completeness_current_v1.csv"
OUT_CSV = GEN_DIR / "enterprise_bootstrap_family_closure_current_v1.csv"

TARGET_FAMILY = "enterprise_bootstrap"
CANONICAL_SCENE = "enterprise.company"
ACCEPTANCE_GUARDS = "authority|canonical_entry|menu_mapping|provider_completeness|suite"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_row() -> dict[str, str | int]:
    authority_rows = [r for r in _read_csv(AUTHORITY_CSV) if str(r.get("family") or "").strip() == TARGET_FAMILY]
    family_row = next((r for r in _read_csv(FAMILY_CSV) if str(r.get("family") or "").strip() == TARGET_FAMILY), None)
    provider_rows = []
    menu_rows = []
    scene_keys = {str(r.get("scene_key") or "").strip() for r in authority_rows}
    for row in _read_csv(PROVIDER_CSV):
        if str(row.get("scene_key") or "").strip() in scene_keys:
            provider_rows.append(row)
    for row in _read_csv(MENU_CSV):
        if str(row.get("resolved_scene_key") or "").strip() in scene_keys:
            menu_rows.append(row)

    if not authority_rows or family_row is None:
        raise RuntimeError(f"family facts missing for {TARGET_FAMILY}")

    frozen_ok = all(str(r.get("status") or "").strip() == "frozen" for r in authority_rows)
    canonical_ok = all(str(r.get("canonical_entry") or "").strip() for r in authority_rows)
    provider_ok = all(str(r.get("completeness_status") or "").strip() == "provider_registered" for r in provider_rows)
    menu_ok = all(
        str(r.get("compatibility_used") or "").strip().lower() == "false"
        for r in menu_rows
        if str(r.get("menu_xmlid") or "").strip()
    )
    closure_status = "CLOSED" if frozen_ok and canonical_ok and provider_ok and menu_ok else "PARTIAL_CLOSED"
    acceptance_status = "all_green" if closure_status == "CLOSED" else "residual_guard_gap"

    required_provider = "|".join(sorted({str(r.get("provider_key") or "").strip() for r in provider_rows if str(r.get("provider_key") or "").strip()}))
    fallback_strategy = "|".join(sorted({str(r.get("native_fallback") or "").strip() for r in authority_rows if str(r.get("native_fallback") or "").strip()}))
    menu_statuses = "|".join(sorted({str(r.get("resolved_scene_key") or "").strip() for r in menu_rows if str(r.get("menu_xmlid") or "").strip()}))

    return {
        "family": TARGET_FAMILY,
        "canonical_scene": CANONICAL_SCENE,
        "scene_count": len(authority_rows),
        "required_provider": required_provider or "provider_tbd",
        "fallback_strategy": fallback_strategy or "none",
        "menu_mapping_status": "bootstrap_menu_mapped_stable" if menu_ok else "bootstrap_menu_mapping_residual",
        "closure_score": 100 if closure_status == "CLOSED" else 80,
        "closure_status": closure_status,
        "primary_gap_type": "none" if closure_status == "CLOSED" else "family_residual_gap",
        "acceptance_status": acceptance_status,
        "blocking_reason": "none" if closure_status == "CLOSED" else "enterprise bootstrap family still has unresolved governance residuals",
        "acceptance_guards": ACCEPTANCE_GUARDS,
        "recommended_next_action": (
            "sync enterprise_bootstrap into the governed family summary perimeter"
            if closure_status == "CLOSED"
            else "reopen enterprise_bootstrap governance on the residual family gap only"
        ),
        "asset_only_closure_possible": "yes" if closure_status == "CLOSED" else "no",
        "runtime_change_required": "no",
        "required_runtime_scope": "none",
        "family_inventory_status": str(family_row.get("governance_status") or "").strip(),
        "menu_scene_coverage": menu_statuses or "none",
    }


def main() -> int:
    try:
        row = build_row()
        _write_csv(
            OUT_CSV,
            [
                "family",
                "canonical_scene",
                "scene_count",
                "required_provider",
                "fallback_strategy",
                "menu_mapping_status",
                "closure_score",
                "closure_status",
                "primary_gap_type",
                "acceptance_status",
                "blocking_reason",
                "acceptance_guards",
                "recommended_next_action",
                "asset_only_closure_possible",
                "runtime_change_required",
                "required_runtime_scope",
                "family_inventory_status",
                "menu_scene_coverage",
            ],
            [row],
        )
    except Exception as exc:
        print(f"[scene_governance_enterprise_bootstrap_family_closure_export] FAIL: {exc}", file=sys.stderr)
        return 1

    print("[scene_governance_enterprise_bootstrap_family_closure_export] PASS")
    print("rows=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
