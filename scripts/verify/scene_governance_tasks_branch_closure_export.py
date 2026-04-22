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
OUT_CSV = GEN_DIR / "tasks_closure_current_v1.csv"

TARGET_SCENES = ("task.center", "task.board")
TASK_ACTION = "project.action_view_all_task"
ACCEPTANCE_GUARDS = "authority|canonical_entry|menu_mapping|task_family_compat|provider_completeness|suite"


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
    if scene_key == "task.center":
        if any(str(row.get("native_action_xmlid") or "").strip() == TASK_ACTION for row in scene_rows):
            return "action_primary_with_route_context"
        return "no_direct_menu_mapping"
    if scene_key == "task.board":
        return "route_only_compat_context"
    return "no_direct_menu_mapping"


def _accepted_menu_context(scene_key: str, menu_mapping_status: str, provider_mode: str) -> bool:
    if provider_mode != "normal":
        return False
    if scene_key == "task.center" and menu_mapping_status == "action_primary_with_route_context":
        return True
    if scene_key == "task.board" and menu_mapping_status == "route_only_compat_context":
        return True
    return False


def _primary_gap_type(scene_key: str, provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode != "normal":
        return "provider_fallback_residual"
    if not accepted_menu_context:
        return "menu_mapping_residual"
    if scene_key == "task.board":
        return "none"
    return "none"


def _blocking_reason(scene_key: str, provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode == "missing":
        return "required provider missing"
    if provider_mode == "fallback_only":
        if scene_key == "task.board":
            return "task.board still depends on fallback-only route compat provider shape"
        return "task.center still depends on fallback-only provider shape"
    if accepted_menu_context:
        return "none"
    if scene_key == "task.board":
        return "task.board compat context is not aligned with current menu mapping facts"
    return "task.center action-primary context is not aligned with current mapping facts"


def _recommended_next_action(scene_key: str, provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode != "normal":
        if scene_key == "task.board":
            return "add dedicated task.board provider ownership before reopening compat or runtime decisions"
        return "add dedicated task.center provider ownership before reopening entry semantics"
    if accepted_menu_context:
        if scene_key == "task.board":
            return "keep task.board as a route-only compat carrier and observe workflow stability"
        return "keep task.center as the action-first task work-center entry and observe workflow stability"
    return "align tasks scene mapping before opening a new runtime slice"


def _runtime_scope(provider_mode: str, accepted_menu_context: bool) -> str:
    if provider_mode == "normal" and accepted_menu_context:
        return "none"
    scopes: list[str] = []
    if provider_mode != "normal":
        scopes.append("provider")
    if not accepted_menu_context:
        scopes.append("menu_interpreter")
    return "|".join(scopes) if scopes else "none"


def _closure_score(*, canonical_entry_status: str, primary_action: str, provider_mode: str, accepted_menu_context: bool) -> int:
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


def _closure_status(*, canonical_entry_status: str, primary_action: str, provider_mode: str, accepted_menu_context: bool) -> str:
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
        provider_mode = _provider_mode(scene_key, provider_rows)
        primary_action = _primary_action(scene_key, authority_row)
        canonical_entry_status = _canonical_entry_status(authority_row)
        fallback_strategy = _fallback_strategy(authority_row)
        menu_mapping_status = _menu_mapping_status(scene_key, menu_rows)
        accepted_menu_context = _accepted_menu_context(scene_key, menu_mapping_status, provider_mode)
        runtime_scope = _runtime_scope(provider_mode, accepted_menu_context)
        rows.append(
            {
                "scene_key": scene_key,
                "user_entry": (
                    "action:project.action_view_all_task"
                    if scene_key == "task.center"
                    else "route:/s/task.board via task-family compat entry"
                ),
                "final_scene": scene_key,
                "primary_action": primary_action,
                "required_provider": _required_provider(scene_key, authority_row, provider_rows),
                "provider_mode": provider_mode,
                "native_action_shared": "true" if primary_action == TASK_ACTION else "false",
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
                "primary_gap_type": _primary_gap_type(scene_key, provider_mode, accepted_menu_context),
                "acceptance_status": "all_green" if accepted_menu_context else "residual_guard_gap",
                "blocking_reason": _blocking_reason(scene_key, provider_mode, accepted_menu_context),
                "acceptance_guards": ACCEPTANCE_GUARDS,
                "recommended_next_action": _recommended_next_action(scene_key, provider_mode, accepted_menu_context),
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
        print("[scene_governance_tasks_branch_closure_export] FAIL")
        print(f"- {exc}")
        return 1

    print("[scene_governance_tasks_branch_closure_export] PASS")
    print(f"scene_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
