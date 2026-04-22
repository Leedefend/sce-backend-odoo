#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GEN_DIR = ROOT / "docs" / "architecture" / "scene-governance" / "assets" / "generated"
AUTHORITY_CSV = GEN_DIR / "scene_authority_matrix_current_v1.csv"
MENU_CSV = GEN_DIR / "menu_scene_mapping_current_v1.csv"
PROVIDER_CSV = GEN_DIR / "provider_completeness_current_v1.csv"
OUT_CSV = GEN_DIR / "payment_approval_closure_current_v1.csv"

TARGET_SCENE = "payments.approval"
TARGET_MENU = "smart_construction_core.menu_sc_tier_review_my_payment_request"
TARGET_ACTION = "smart_construction_core.action_sc_tier_review_my_payment_request"
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
    authority_rows = _read_csv(AUTHORITY_CSV)
    menu_rows = _read_csv(MENU_CSV)
    provider_rows = _read_csv(PROVIDER_CSV)

    authority_row = next((row for row in authority_rows if str(row.get("scene_key") or "").strip() == TARGET_SCENE), None)
    if authority_row is None:
        raise RuntimeError(f"authority row missing for {TARGET_SCENE}")

    provider_row = next((row for row in provider_rows if str(row.get("scene_key") or "").strip() == TARGET_SCENE), None)
    menu_row = next(
        (
            row
            for row in menu_rows
            if str(row.get("resolved_scene_key") or "").strip() == TARGET_SCENE
            and str(row.get("menu_xmlid") or "").strip() == TARGET_MENU
        ),
        None,
    )

    canonical_entry = str(authority_row.get("canonical_entry") or "").strip()
    primary_action = str(authority_row.get("action_binding") or "").strip()
    provider_key = ""
    provider_mode = "missing"
    if provider_row is not None:
        provider_key = str(provider_row.get("provider_key") or "").strip()
        completeness = str(provider_row.get("completeness_status") or "").strip()
        if completeness == "provider_registered":
            provider_mode = "normal"
        elif completeness == "fallback_only":
            provider_mode = "fallback_only"

    canonical_entry_status = "explicit_canonical_entry" if canonical_entry else "missing_canonical_entry"
    menu_mapping_status = "approval_menu_bound" if menu_row is not None else "approval_menu_missing"
    accepted_menu_context = menu_row is not None and str(menu_row.get("compatibility_used") or "").strip().lower() == "false"
    closure_status = "CLOSED"
    primary_gap_type = "none"
    acceptance_status = "all_green"
    blocking_reason = "none"
    asset_only_closure_possible = "yes"
    runtime_change_required = "no"
    required_runtime_scope = "none"
    closure_score = 100

    if canonical_entry_status != "explicit_canonical_entry" or not primary_action or provider_mode == "missing":
        closure_status = "BLOCKED"
        acceptance_status = "residual_guard_gap"
        asset_only_closure_possible = "no"
        runtime_change_required = "yes"
        required_runtime_scope = "provider|menu_interpreter"
        primary_gap_type = "blocking_identity_or_provider_gap"
        blocking_reason = "required canonical entry, primary action, or provider is missing"
        closure_score = 40
    elif provider_mode != "normal" or not accepted_menu_context:
        closure_status = "PARTIAL_CLOSED"
        acceptance_status = "residual_guard_gap"
        asset_only_closure_possible = "no"
        runtime_change_required = "yes"
        required_runtime_scope = "provider" if provider_mode != "normal" else "menu_interpreter"
        primary_gap_type = "provider_fallback_residual" if provider_mode != "normal" else "menu_mapping_residual"
        blocking_reason = (
            "approval scene still depends on fallback-only provider shape"
            if provider_mode != "normal"
            else "approval menu mapping does not yet resolve as dedicated scene authority"
        )
        closure_score = 80 if provider_mode != "normal" else 85

    return {
        "scene_key": TARGET_SCENE,
        "user_entry": f"menu:{TARGET_MENU}",
        "final_scene": TARGET_SCENE,
        "primary_action": primary_action or TARGET_ACTION,
        "required_provider": provider_key or "provider_tbd",
        "provider_mode": provider_mode,
        "native_action_shared": "false",
        "canonical_entry_status": canonical_entry_status,
        "fallback_strategy": str(authority_row.get("native_fallback") or "").strip() or "undefined",
        "menu_mapping_status": menu_mapping_status,
        "closure_score": closure_score,
        "closure_status": closure_status,
        "primary_gap_type": primary_gap_type,
        "acceptance_status": acceptance_status,
        "blocking_reason": blocking_reason,
        "acceptance_guards": ACCEPTANCE_GUARDS,
        "recommended_next_action": (
            "keep payments.approval as the approval-specific canonical workbench entry"
            if closure_status == "CLOSED"
            else "reopen payment approval governance on the residual gap only"
        ),
        "asset_only_closure_possible": asset_only_closure_possible,
        "runtime_change_required": runtime_change_required,
        "required_runtime_scope": required_runtime_scope,
    }


def main() -> int:
    try:
        row = build_row()
        _write_csv(
            OUT_CSV,
            [
                "scene_key",
                "user_entry",
                "final_scene",
                "primary_action",
                "required_provider",
                "provider_mode",
                "native_action_shared",
                "canonical_entry_status",
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
            ],
            [row],
        )
    except Exception as exc:
        print(f"[scene_governance_payment_approval_branch_closure_export] FAIL: {exc}", file=sys.stderr)
        return 1

    print("[scene_governance_payment_approval_branch_closure_export] PASS")
    print("rows=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
