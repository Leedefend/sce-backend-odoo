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
OUT_CSV = GEN_DIR / "finance_center_closure_current_v1.csv"

TARGET_SCENES = ("finance.center", "finance.workspace")
SHARED_ROOT_ACTION = "smart_construction_core.action_sc_finance_dashboard"
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


def _provider_mode(scene_key: str, provider_rows: list[dict[str, str]]) -> str:
    row = next((item for item in provider_rows if str(item.get("scene_key") or "").strip() == scene_key), None)
    if row is None:
        return "missing"
    completeness = str(row.get("completeness_status") or "").strip()
    if completeness == "provider_registered":
        return "normal"
    if completeness == "fallback_only":
        return "fallback_only"
    return "missing"


def _required_provider(scene_key: str, authority_row: dict[str, str], provider_rows: list[dict[str, str]]) -> str:
    authority_provider = str(authority_row.get("provider_owner") or "").strip()
    if authority_provider and authority_provider != "provider_tbd":
        return authority_provider
    provider_row = next((item for item in provider_rows if str(item.get("scene_key") or "").strip() == scene_key), None)
    if provider_row and str(provider_row.get("provider_key") or "").strip():
        return str(provider_row.get("provider_key") or "").strip()
    return "provider_tbd"


def _primary_action(scene_key: str, authority_row: dict[str, str]) -> str:
    action_binding = str(authority_row.get("action_binding") or "").strip()
    if action_binding:
        return action_binding
    canonical_entry = str(authority_row.get("canonical_entry") or "").strip()
    if canonical_entry:
        return f"route:{canonical_entry}"
    return ""


def _canonical_entry_status(authority_row: dict[str, str]) -> str:
    return "explicit_canonical_entry" if str(authority_row.get("canonical_entry") or "").strip() else "missing_canonical_entry"


def _fallback_strategy(authority_row: dict[str, str]) -> str:
    return str(authority_row.get("native_fallback") or "").strip() or "undefined"


def _menu_mapping_status(scene_key: str, menu_rows: list[dict[str, str]]) -> str:
    scene_rows = [row for row in menu_rows if str(row.get("resolved_scene_key") or "").strip() == scene_key]
    if scene_key == "finance.center":
        if scene_rows:
            return "menu_mapped_stable"
        return "no_direct_menu_mapping"
    if scene_key == "finance.workspace":
        return "route_primary_with_root_menu_context"
    return "no_direct_menu_mapping"


def _shared_root_compatibility_used(scene_key: str) -> str:
    if scene_key in TARGET_SCENES:
        return "true"
    return "false"


def _shared_root_closure_status(scene_key: str) -> str:
    if scene_key == "finance.center":
        return "root_owner_retained"
    if scene_key == "finance.workspace":
        return "route_plus_menu_compat"
    return "not_applicable"


def _accepted_menu_context(scene_key: str, menu_mapping_status: str, provider_mode: str, native_action_shared: str) -> bool:
    if provider_mode != "normal":
        return False
    if scene_key == "finance.center" and menu_mapping_status == "menu_mapped_stable":
        return True
    if scene_key == "finance.workspace" and menu_mapping_status == "route_primary_with_root_menu_context" and native_action_shared == "false":
        return True
    return False


def _primary_gap_type(provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode != "normal":
        return "provider_fallback_residual"
    if not accepted_menu_context:
        return "menu_mapping_residual"
    return "none"


def _blocking_reason(scene_key: str, provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode == "missing":
        return "required provider missing"
    if provider_mode == "fallback_only":
        return "provider fallback-only"
    if accepted_menu_context:
        return "none"
    if scene_key == "finance.workspace":
        return "workspace route-plus-menu context is not aligned with current menu mapping facts"
    return "finance root menu mapping not aligned"


def _recommended_next_action(scene_key: str, accepted_menu_context: bool) -> str:
    if accepted_menu_context:
        if scene_key == "finance.center":
            return "keep finance.center as canonical root owner and observe downstream approval-adjacent follow-up scenes"
        return "keep finance.workspace on route-primary workbench semantics and observe follow-up workflow stability"
    if scene_key == "finance.workspace":
        return "align workspace route-plus-menu context before opening another runtime slice"
    return "align finance root menu mapping before opening another runtime slice"


def _runtime_scope(provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode == "normal" and accepted_menu_context:
        return "none"
    scopes: list[str] = []
    if provider_mode != "normal":
        scopes.append("provider")
    if not accepted_menu_context:
        scopes.append("menu_interpreter")
    return "|".join(scopes) if scopes else "none"


def _closure_score(
    *,
    canonical_entry_status: str,
    primary_action: str,
    provider_mode: str,
    accepted_menu_context: bool,
) -> int:
    score = 100
    if canonical_entry_status != "explicit_canonical_entry":
        score -= 30
    if not primary_action:
        score -= 25
    if provider_mode == "fallback_only":
        score -= 20
    elif provider_mode == "missing":
        score -= 40
    if not accepted_menu_context:
        score -= 15
    return max(score, 0)


def _closure_status(
    *,
    canonical_entry_status: str,
    primary_action: str,
    provider_mode: str,
    accepted_menu_context: bool,
) -> str:
    if canonical_entry_status != "explicit_canonical_entry" or not primary_action or provider_mode == "missing":
        return "BLOCKED"
    if provider_mode == "normal" and accepted_menu_context:
        return "CLOSED"
    return "PARTIAL_CLOSED"


def build_rows() -> list[dict[str, str | int]]:
    authority_rows = _read_csv(AUTHORITY_CSV)
    menu_rows = _read_csv(MENU_CSV)
    provider_rows = _read_csv(PROVIDER_CSV)

    authority_index = {
        str(row.get("scene_key") or "").strip(): row
        for row in authority_rows
        if str(row.get("scene_key") or "").strip() in TARGET_SCENES
    }
    if set(authority_index) != set(TARGET_SCENES):
        missing = sorted(set(TARGET_SCENES) - set(authority_index))
        raise RuntimeError(f"authority rows missing for: {', '.join(missing)}")

    rows: list[dict[str, str | int]] = []
    for scene_key in TARGET_SCENES:
        authority_row = authority_index[scene_key]
        primary_action = _primary_action(scene_key, authority_row)
        provider_mode = _provider_mode(scene_key, provider_rows)
        required_provider = _required_provider(scene_key, authority_row, provider_rows)
        native_action_shared = "true" if primary_action == SHARED_ROOT_ACTION else "false"
        canonical_entry_status = _canonical_entry_status(authority_row)
        fallback_strategy = _fallback_strategy(authority_row)
        menu_mapping_status = _menu_mapping_status(scene_key, menu_rows)
        shared_root_compatibility_used = _shared_root_compatibility_used(scene_key)
        shared_root_closure_status = _shared_root_closure_status(scene_key)
        accepted_menu_context = _accepted_menu_context(scene_key, menu_mapping_status, provider_mode, native_action_shared)
        acceptance_status = "all_green" if accepted_menu_context else "residual_guard_gap"
        runtime_scope = _runtime_scope(provider_mode, accepted_menu_context)
        rows.append(
            {
                "scene_key": scene_key,
                "user_entry": (
                    "menu:smart_construction_core.menu_sc_finance_center"
                    if scene_key == "finance.center"
                    else "route:/s/finance.workspace via finance.center follow-up"
                ),
                "final_scene": scene_key,
                "primary_action": primary_action,
                "required_provider": required_provider,
                "provider_mode": provider_mode,
                "native_action_shared": native_action_shared,
                "canonical_entry_status": canonical_entry_status,
                "fallback_strategy": fallback_strategy,
                "menu_mapping_status": menu_mapping_status,
                "closure_score": _closure_score(
                    canonical_entry_status=canonical_entry_status,
                    primary_action=primary_action,
                    provider_mode=provider_mode,
                    accepted_menu_context=accepted_menu_context,
                ),
                "closure_status": _closure_status(
                    canonical_entry_status=canonical_entry_status,
                    primary_action=primary_action,
                    provider_mode=provider_mode,
                    accepted_menu_context=accepted_menu_context,
                ),
                "primary_gap_type": _primary_gap_type(provider_mode, accepted_menu_context),
                "acceptance_status": acceptance_status,
                "blocking_reason": _blocking_reason(scene_key, provider_mode, accepted_menu_context),
                "acceptance_guards": ACCEPTANCE_GUARDS,
                "recommended_next_action": _recommended_next_action(scene_key, accepted_menu_context),
                "asset_only_closure_possible": "no" if runtime_scope != "none" else "yes",
                "runtime_change_required": "yes" if runtime_scope != "none" else "no",
                "required_runtime_scope": runtime_scope,
                "shared_root_compatibility_used": shared_root_compatibility_used,
                "shared_root_closure_status": shared_root_closure_status,
            }
        )
    return rows


def main() -> int:
    try:
        rows = build_rows()
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
                "shared_root_compatibility_used",
                "shared_root_closure_status",
            ],
            rows,
        )
    except Exception as exc:
        print("[scene_governance_finance_branch_closure_export] FAIL")
        print(f"- {exc}")
        return 1

    print("[scene_governance_finance_branch_closure_export] PASS")
    print(f"scene_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
