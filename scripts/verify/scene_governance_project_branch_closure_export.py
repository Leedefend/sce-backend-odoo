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
OUT_CSV = GEN_DIR / "projects_ledger_detail_closure_current_v1.csv"

TARGET_SCENES = ("projects.ledger", "projects.detail")
SHARED_NATIVE_ACTION = "smart_construction_core.action_sc_project_kanban_lifecycle"
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


def _menu_mapping_status(scene_key: str, menu_rows: list[dict[str, str]]) -> str:
    scene_rows = [row for row in menu_rows if str(row.get("resolved_scene_key") or "").strip() == scene_key]
    if scene_key == "projects.detail":
        return "route_primary_with_menu_compat_context"
    if scene_key == "projects.ledger":
        has_menu_mapping = any(str(row.get("menu_xmlid") or "").strip() for row in scene_rows)
        has_action_compat = any(str(row.get("compatibility_used") or "").strip().lower() == "true" for row in scene_rows)
        if has_menu_mapping and has_action_compat:
            return "menu_mapped_stable"
    if any(str(row.get("compatibility_used") or "").strip().lower() == "true" for row in scene_rows):
        return "menu_mapped_with_action_compat_residual"
    if scene_rows:
        return "menu_mapped_stable"
    return "no_direct_menu_mapping"


def _accepted_menu_context(scene_key: str, menu_mapping_status: str, native_action_shared: str) -> bool:
    if scene_key == "projects.ledger" and menu_mapping_status == "menu_mapped_stable":
        return True
    if scene_key == "projects.detail" and menu_mapping_status == "route_primary_with_menu_compat_context" and native_action_shared != "true":
        return True
    return False


def _primary_action(scene_key: str, authority_row: dict[str, str]) -> str:
    action_binding = str(authority_row.get("action_binding") or "").strip()
    if action_binding:
        return action_binding
    canonical_entry = str(authority_row.get("canonical_entry") or "").strip()
    if scene_key == "projects.detail" and canonical_entry:
        return f"route:{canonical_entry}"
    return canonical_entry


def _canonical_entry_status(authority_row: dict[str, str]) -> str:
    canonical_entry = str(authority_row.get("canonical_entry") or "").strip()
    if canonical_entry:
        return "explicit_canonical_entry"
    return "missing_canonical_entry"


def _fallback_strategy(authority_row: dict[str, str]) -> str:
    return str(authority_row.get("native_fallback") or "").strip() or "undefined"


def _primary_gap_type(scene_key: str, provider_mode: str, native_action_shared: str, menu_mapping_status: str) -> str:
    if _accepted_menu_context(scene_key, menu_mapping_status, native_action_shared):
        return "none"
    if scene_key == "projects.detail" and native_action_shared == "true":
        return "shared_native_action_residual"
    if scene_key == "projects.detail":
        return "none"
    if scene_key == "projects.ledger" and menu_mapping_status == "menu_mapped_stable":
        return "none"
    if provider_mode != "normal":
        return "provider_fallback_residual"
    if native_action_shared == "true":
        return "shared_native_action_residual"
    if "compat" in menu_mapping_status:
        return "menu_mapping_residual"
    return "none"


def _blocking_reason(
    scene_key: str,
    provider_mode: str,
    native_action_shared: str,
    menu_mapping_status: str,
) -> str:
    if _accepted_menu_context(scene_key, menu_mapping_status, native_action_shared) and provider_mode == "normal":
        return "none"
    reasons: list[str] = []
    if provider_mode == "fallback_only":
        reasons.append("provider fallback-only")
    elif provider_mode == "missing":
        reasons.append("required provider missing")
    if native_action_shared == "true" and scene_key != "projects.ledger":
        reasons.append("shared native action residual")
    if "compat" in menu_mapping_status or menu_mapping_status.startswith("no_direct_menu_mapping"):
        reasons.append("menu mapping residual")
    if not reasons:
        return "none"
    if scene_key == "projects.detail" and "shared native action residual" in reasons:
        return "shared native action still carries detail semantics"
    return "; ".join(reasons)


def _recommended_next_action(scene_key: str, provider_mode: str, native_action_shared: str) -> str:
    if scene_key == "projects.ledger":
        if provider_mode != "normal":
            return "add dedicated ledger provider ownership before changing broader project family runtime"
        return "keep ledger on native-parity authority and observe runtime behavior before opening a new runtime slice"
    if scene_key == "projects.detail":
        if native_action_shared != "true":
            return "keep detail on route-primary authority and observe remaining runtime behavior before opening a new runtime slice"
        return "split detail semantics from the shared native action and add dedicated detail provider ownership"
    return "review closure residuals"


def _runtime_scope(scene_key: str, provider_mode: str, native_action_shared: str, menu_mapping_status: str) -> str:
    if _accepted_menu_context(scene_key, menu_mapping_status, native_action_shared) and provider_mode == "normal":
        return "none"
    scopes: list[str] = []
    if provider_mode != "normal":
        scopes.append("provider")
    if (native_action_shared == "true" and scene_key != "projects.ledger") or "compat" in menu_mapping_status or menu_mapping_status.startswith("no_direct_menu_mapping"):
        scopes.append("menu_interpreter")
    if scene_key == "projects.detail" and native_action_shared == "true":
        scopes.append("orchestrator")
    return "|".join(dict.fromkeys(scopes)) if scopes else "none"


def _closure_score(
    scene_key: str,
    canonical_entry_status: str,
    final_scene: str,
    primary_action: str,
    provider_mode: str,
    native_action_shared: str,
    fallback_strategy: str,
    menu_mapping_status: str,
    acceptance_status: str,
) -> int:
    score = 100
    if canonical_entry_status != "explicit_canonical_entry":
        score -= 30
    if not final_scene:
        score -= 30
    if not primary_action:
        score -= 25
    if provider_mode == "fallback_only":
        score -= 20
    elif provider_mode == "missing":
        score -= 40
    accepted_context = _accepted_menu_context(scene_key, menu_mapping_status, native_action_shared)
    if native_action_shared == "true" and not accepted_context:
        score -= 15
    if not fallback_strategy or fallback_strategy == "undefined":
        score -= 10
    if "compat" in menu_mapping_status and not accepted_context:
        score -= 10
    elif menu_mapping_status.startswith("no_direct_menu_mapping"):
        score -= 12
    if acceptance_status != "all_green":
        score -= 5
    return max(score, 0)


def _closure_status(
    scene_key: str,
    canonical_entry_status: str,
    final_scene: str,
    primary_action: str,
    provider_mode: str,
    fallback_strategy: str,
    menu_mapping_status: str,
    acceptance_status: str,
) -> str:
    accepted_context = _accepted_menu_context(scene_key, menu_mapping_status, "true" if primary_action == SHARED_NATIVE_ACTION else "false")
    if (
        not final_scene
        or not primary_action
        or provider_mode == "missing"
        or canonical_entry_status != "explicit_canonical_entry"
        or acceptance_status == "guard_failed"
    ):
        return "BLOCKED"
    if (
        provider_mode == "normal"
        and fallback_strategy != "undefined"
        and (menu_mapping_status == "menu_mapped_stable" or accepted_context)
        and acceptance_status == "all_green"
    ):
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
        final_scene = scene_key
        provider_mode = _provider_mode(scene_key, provider_rows)
        required_provider = _required_provider(scene_key, authority_row, provider_rows)
        native_action_shared = "true" if primary_action == SHARED_NATIVE_ACTION else "false"
        canonical_entry_status = _canonical_entry_status(authority_row)
        fallback_strategy = _fallback_strategy(authority_row)
        menu_mapping_status = _menu_mapping_status(scene_key, menu_rows)
        acceptance_status = "all_green"
        if not _accepted_menu_context(scene_key, menu_mapping_status, native_action_shared):
            if provider_mode != "normal" or native_action_shared == "true" or "compat" in menu_mapping_status or menu_mapping_status.startswith("no_direct_menu_mapping"):
                acceptance_status = "residual_guard_gap"
        closure_score = _closure_score(
            scene_key=scene_key,
            canonical_entry_status=canonical_entry_status,
            final_scene=final_scene,
            primary_action=primary_action,
            provider_mode=provider_mode,
            native_action_shared=native_action_shared,
            fallback_strategy=fallback_strategy,
            menu_mapping_status=menu_mapping_status,
            acceptance_status=acceptance_status,
        )
        closure_status = _closure_status(
            scene_key=scene_key,
            canonical_entry_status=canonical_entry_status,
            final_scene=final_scene,
            primary_action=primary_action,
            provider_mode=provider_mode,
            fallback_strategy=fallback_strategy,
            menu_mapping_status=menu_mapping_status,
            acceptance_status=acceptance_status,
        )
        primary_gap_type = _primary_gap_type(scene_key, provider_mode, native_action_shared, menu_mapping_status)
        blocking_reason = _blocking_reason(scene_key, provider_mode, native_action_shared, menu_mapping_status)
        recommended_next_action = _recommended_next_action(scene_key, provider_mode, native_action_shared)
        runtime_scope = _runtime_scope(scene_key, provider_mode, native_action_shared, menu_mapping_status)
        rows.append(
            {
                "scene_key": scene_key,
                "user_entry": (
                    "menu:smart_construction_core.menu_sc_project_project"
                    if scene_key == "projects.ledger"
                    else "route:/s/projects.detail via projects.ledger transition"
                ),
                "final_scene": final_scene,
                "primary_action": primary_action,
                "required_provider": required_provider,
                "provider_mode": provider_mode,
                "native_action_shared": native_action_shared,
                "canonical_entry_status": canonical_entry_status,
                "fallback_strategy": fallback_strategy,
                "menu_mapping_status": menu_mapping_status,
                "closure_score": closure_score,
                "closure_status": closure_status,
                "primary_gap_type": primary_gap_type,
                "acceptance_status": acceptance_status,
                "blocking_reason": blocking_reason,
                "acceptance_guards": ACCEPTANCE_GUARDS,
                "recommended_next_action": recommended_next_action,
                "asset_only_closure_possible": "no" if runtime_scope != "none" else "yes",
                "runtime_change_required": "yes" if runtime_scope != "none" else "no",
                "required_runtime_scope": runtime_scope,
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
            ],
            rows,
        )
    except Exception as exc:
        print("[scene_governance_project_branch_closure_export] FAIL")
        print(f"- {exc}")
        return 1

    print("[scene_governance_project_branch_closure_export] PASS")
    print(f"scene_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
