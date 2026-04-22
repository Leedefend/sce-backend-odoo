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
SCORE_CSV = GEN_DIR / "family_priority_score_current_v1.csv"
OUT_CSV = GEN_DIR / "high_priority_family_user_flow_closure_current_v1.csv"
FINANCE_BRANCH_CLOSURE_CSV = GEN_DIR / "finance_center_closure_current_v1.csv"
TASKS_BRANCH_CLOSURE_CSV = GEN_DIR / "tasks_closure_current_v1.csv"
PROJECTS_BRANCH_CLOSURE_CSV = GEN_DIR / "projects_ledger_detail_closure_current_v1.csv"
CONTRACTS_BRANCH_CLOSURE_CSV = GEN_DIR / "contracts_closure_current_v1.csv"
PAYMENT_APPROVAL_BRANCH_CLOSURE_CSV = GEN_DIR / "payment_approval_closure_current_v1.csv"
PAYMENT_ENTRY_BRANCH_CLOSURE_CSV = GEN_DIR / "payment_entry_closure_current_v1.csv"
ENTERPRISE_BOOTSTRAP_FAMILY_CLOSURE_CSV = GEN_DIR / "enterprise_bootstrap_family_closure_current_v1.csv"

TOP_FAMILY_COUNT = 3
GOVERNED_SUMMARY_FAMILIES = (
    "projects",
    "finance_center",
    "tasks",
    "contracts",
    "payment_approval",
)

FAMILY_PLAN_MAP = {
    "projects": {
        "menu_mapping_anomaly": "projects.detail still rides the shared project ledger native action as compatibility-only semantics",
        "planned_closure_action": "extract explicit project user-flow closure assets for list, ledger, detail, and intake instead of relying on shared native interpretation",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
    "contracts": {
        "menu_mapping_anomaly": "contracts branch closure is not yet synced into the family summary surface",
        "planned_closure_action": "extract and sync contract root/workspace user-flow closure facts before opening the monitor slice",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
    "finance_center": {
        "menu_mapping_anomaly": "finance root and finance workspace still converge on the shared finance dashboard action and need explicit user-flow closure",
        "planned_closure_action": "extract finance root and workspace user-flow closure assets around root entry, workspace, and approval-adjacent follow-up",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
    "tasks": {
        "menu_mapping_anomaly": "task family still has no dedicated native menu root and depends on direct compat interpretation for task.center",
        "planned_closure_action": "turn task family from compatibility-stable into workflow-stable by exporting explicit center and board user-flow closure facts",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|task_family_compat|provider_completeness|suite",
    },
    "payment_approval": {
        "menu_mapping_anomaly": "payment approval branch closure is not yet synced into the family summary surface",
        "planned_closure_action": "sync the dedicated approval branch closure asset into the family summary and keep approval semantics scene-first",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
    "payment_entry": {
        "menu_mapping_anomaly": "payment entry branch closure is not yet synced into the family summary surface",
        "planned_closure_action": "sync the dedicated payment-entry branch closure asset into the family summary and keep payment-request list semantics scene-first",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
    "enterprise_bootstrap": {
        "menu_mapping_anomaly": "enterprise bootstrap family closure is not yet synced into the family summary surface",
        "planned_closure_action": "sync the dedicated enterprise bootstrap family closure asset into the family summary and keep bootstrap semantics scene-first",
        "acceptance_guards": "authority|canonical_entry|menu_mapping|provider_completeness|suite",
    },
}


def _read_optional_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return _read_csv(path)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str | int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _format_entry(row: dict[str, str]) -> str:
    menu_binding = str(row.get("menu_binding") or "").strip()
    action_binding = str(row.get("action_binding") or "").strip()
    canonical_entry = str(row.get("canonical_entry") or "").strip()
    if menu_binding:
        return f"menu:{menu_binding}"
    if action_binding:
        return f"action:{action_binding}"
    return f"route:{canonical_entry}"


def _format_primary_action(row: dict[str, str]) -> str:
    action_binding = str(row.get("action_binding") or "").strip()
    canonical_entry = str(row.get("canonical_entry") or "").strip()
    if action_binding:
        return action_binding
    return canonical_entry or "tbd"


def _build_provider_requirement(
    canonical_row: dict[str, str],
    provider_rows: list[dict[str, str]],
) -> str:
    provider_owner = str(canonical_row.get("provider_owner") or "").strip()
    if provider_owner and provider_owner != "provider_tbd":
        return provider_owner
    registered = sorted(
        {
            str(row.get("provider_key") or "").strip()
            for row in provider_rows
            if str(row.get("provider_registered") or "").strip().lower() == "true"
            and str(row.get("provider_key") or "").strip()
        }
    )
    if registered:
        return "|".join(registered)
    return "provider_tbd"


def _build_fallback_strategy(authority_rows: list[dict[str, str]]) -> str:
    fallbacks = []
    for row in authority_rows:
        value = str(row.get("native_fallback") or "").strip()
        if value and value not in fallbacks:
            fallbacks.append(value)
    return "|".join(fallbacks) if fallbacks else "none"


def _build_authority_status(authority_rows: list[dict[str, str]]) -> str:
    frozen_count = sum(1 for row in authority_rows if str(row.get("status") or "").strip() == "frozen")
    return f"registry authority frozen for {frozen_count}/{len(authority_rows)} scenes"


def _build_canonical_status(authority_rows: list[dict[str, str]], canonical_scene: str) -> str:
    canonical_count = sum(1 for row in authority_rows if str(row.get("canonical_entry") or "").strip())
    compat_count = sum(
        1
        for row in authority_rows
        if "compat" in str(row.get("native_fallback") or "").strip().lower()
        or "shared" in str(row.get("native_fallback") or "").strip().lower()
    )
    return (
        f"canonical routes frozen for {canonical_count}/{len(authority_rows)} scenes; "
        f"canonical scene={canonical_scene}; residual compat carriers={compat_count}"
    )


def _build_provider_gap(provider_rows: list[dict[str, str]]) -> str:
    fallback_only = [row["scene_key"] for row in provider_rows if str(row.get("completeness_status") or "") == "fallback_only"]
    missing = [row["scene_key"] for row in provider_rows if str(row.get("completeness_status") or "") == "missing"]
    registered = [row["scene_key"] for row in provider_rows if str(row.get("completeness_status") or "") == "provider_registered"]
    return (
        f"provider_registered={len(registered)};"
        f"fallback_only={len(fallback_only)}:{'|'.join(fallback_only) if fallback_only else 'none'};"
        f"missing={len(missing)}:{'|'.join(missing) if missing else 'none'}"
    )


def _build_acceptance_status(menu_rows: list[dict[str, str]], provider_rows: list[dict[str, str]]) -> str:
    compatibility_count = sum(
        1 for row in menu_rows if str(row.get("compatibility_used") or "").strip().lower() == "true"
    )
    missing_provider_count = sum(
        1 for row in provider_rows if str(row.get("completeness_status") or "").strip() == "missing"
    )
    fallback_only_count = sum(
        1 for row in provider_rows if str(row.get("completeness_status") or "").strip() == "fallback_only"
    )
    if missing_provider_count:
        return "guarded_missing_provider"
    if compatibility_count or fallback_only_count:
        return "guarded_with_residual_compat"
    return "guarded_ready"


def _load_finance_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(FINANCE_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    scene_rows = [row for row in rows if str(row.get("scene_key") or "").strip() in {"finance.center", "finance.workspace"}]
    if len(scene_rows) != 2:
        return {}
    provider_values = []
    fallback_values = []
    shared_status_values = []
    recommended_actions = []
    all_closed = True
    all_green = True
    runtime_required = False
    for row in scene_rows:
        required_provider = str(row.get("required_provider") or "").strip()
        fallback_strategy = str(row.get("fallback_strategy") or "").strip()
        shared_status = str(row.get("shared_root_closure_status") or "").strip()
        recommended = str(row.get("recommended_next_action") or "").strip()
        if required_provider and required_provider not in provider_values:
            provider_values.append(required_provider)
        if fallback_strategy and fallback_strategy not in fallback_values:
            fallback_values.append(fallback_strategy)
        if shared_status and shared_status not in shared_status_values:
            shared_status_values.append(shared_status)
        if recommended and recommended not in recommended_actions:
            recommended_actions.append(recommended)
        if str(row.get("closure_status") or "").strip() != "CLOSED":
            all_closed = False
        if str(row.get("acceptance_status") or "").strip() != "all_green":
            all_green = False
        if str(row.get("runtime_change_required") or "").strip() == "yes":
            runtime_required = True
    acceptance_status = "guarded_ready" if all_closed and all_green and not runtime_required else "guarded_with_residual_compat"
    return {
        "required_provider": "|".join(provider_values) if provider_values else "provider_tbd",
        "fallback_strategy": "|".join(fallback_values) if fallback_values else "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "finance branch closure is closed; shared-root semantics are frozen as "
            + "|".join(shared_status_values)
            if shared_status_values
            else "finance branch closure is closed"
        ),
        "provider_gap": "provider_registered=2;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "finance_center branch closure is already closed; keep family summary synced to the dedicated finance branch asset and observe approval-adjacent follow-up scenes"
            if recommended_actions
            else "keep finance_center family summary synced to the dedicated branch closure asset"
        ),
    }


def _load_tasks_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(TASKS_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    scene_rows = [row for row in rows if str(row.get("scene_key") or "").strip() in {"task.center", "task.board"}]
    if len(scene_rows) != 2:
        return {}
    provider_values = []
    fallback_values = []
    menu_status_values = []
    recommended_actions = []
    all_closed = True
    all_green = True
    runtime_required = False
    for row in scene_rows:
        required_provider = str(row.get("required_provider") or "").strip()
        fallback_strategy = str(row.get("fallback_strategy") or "").strip()
        menu_status = str(row.get("menu_mapping_status") or "").strip()
        recommended = str(row.get("recommended_next_action") or "").strip()
        if required_provider and required_provider not in provider_values:
            provider_values.append(required_provider)
        if fallback_strategy and fallback_strategy not in fallback_values:
            fallback_values.append(fallback_strategy)
        if menu_status and menu_status not in menu_status_values:
            menu_status_values.append(menu_status)
        if recommended and recommended not in recommended_actions:
            recommended_actions.append(recommended)
        if str(row.get("closure_status") or "").strip() != "CLOSED":
            all_closed = False
        if str(row.get("acceptance_status") or "").strip() != "all_green":
            all_green = False
        if str(row.get("runtime_change_required") or "").strip() == "yes":
            runtime_required = True
    acceptance_status = "guarded_ready" if all_closed and all_green and not runtime_required else "guarded_with_residual_compat"
    return {
        "required_provider": "|".join(provider_values) if provider_values else "provider_tbd",
        "fallback_strategy": "|".join(fallback_values) if fallback_values else "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "tasks branch closure is closed; scene semantics are frozen as "
            + "|".join(menu_status_values)
            if menu_status_values
            else "tasks branch closure is closed"
        ),
        "provider_gap": "provider_registered=2;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "tasks branch closure is already closed; keep family summary synced to the dedicated tasks branch asset and observe downstream workflow follow-up scenes"
            if recommended_actions
            else "keep tasks family summary synced to the dedicated branch closure asset"
        ),
    }


def _load_projects_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(PROJECTS_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    scene_rows = [row for row in rows if str(row.get("scene_key") or "").strip() in {"projects.ledger", "projects.detail"}]
    if len(scene_rows) != 2:
        return {}
    provider_values = []
    fallback_values = []
    menu_status_values = []
    recommended_actions = []
    all_closed = True
    all_green = True
    runtime_required = False
    for row in scene_rows:
        required_provider = str(row.get("required_provider") or "").strip()
        fallback_strategy = str(row.get("fallback_strategy") or "").strip()
        menu_status = str(row.get("menu_mapping_status") or "").strip()
        recommended = str(row.get("recommended_next_action") or "").strip()
        if required_provider and required_provider not in provider_values:
            provider_values.append(required_provider)
        if fallback_strategy and fallback_strategy not in fallback_values:
            fallback_values.append(fallback_strategy)
        if menu_status and menu_status not in menu_status_values:
            menu_status_values.append(menu_status)
        if recommended and recommended not in recommended_actions:
            recommended_actions.append(recommended)
        if str(row.get("closure_status") or "").strip() != "CLOSED":
            all_closed = False
        if str(row.get("acceptance_status") or "").strip() != "all_green":
            all_green = False
        if str(row.get("runtime_change_required") or "").strip() == "yes":
            runtime_required = True
    acceptance_status = "guarded_ready" if all_closed and all_green and not runtime_required else "guarded_with_residual_compat"
    return {
        "required_provider": "|".join(provider_values) if provider_values else "provider_tbd",
        "fallback_strategy": "|".join(fallback_values) if fallback_values else "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "projects branch closure is closed; scene semantics are frozen as "
            + "|".join(menu_status_values)
            if menu_status_values
            else "projects branch closure is closed"
        ),
        "provider_gap": "provider_registered=2;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "projects branch closure is already closed; keep family summary synced to the dedicated projects branch asset and observe downstream list/intake follow-up scenes"
            if recommended_actions
            else "keep projects family summary synced to the dedicated branch closure asset"
        ),
    }


def _load_contracts_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(CONTRACTS_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    scene_rows = [row for row in rows if str(row.get("scene_key") or "").strip() in {"contract.center", "contracts.workspace"}]
    if len(scene_rows) != 2:
        return {}
    provider_values = []
    fallback_values = []
    menu_status_values = []
    recommended_actions = []
    all_closed = True
    all_green = True
    runtime_required = False
    for row in scene_rows:
        required_provider = str(row.get("required_provider") or "").strip()
        fallback_strategy = str(row.get("fallback_strategy") or "").strip()
        menu_status = str(row.get("menu_mapping_status") or "").strip()
        recommended = str(row.get("recommended_next_action") or "").strip()
        if required_provider and required_provider not in provider_values:
            provider_values.append(required_provider)
        if fallback_strategy and fallback_strategy not in fallback_values:
            fallback_values.append(fallback_strategy)
        if menu_status and menu_status not in menu_status_values:
            menu_status_values.append(menu_status)
        if recommended and recommended not in recommended_actions:
            recommended_actions.append(recommended)
        if str(row.get("closure_status") or "").strip() != "CLOSED":
            all_closed = False
        if str(row.get("acceptance_status") or "").strip() != "all_green":
            all_green = False
        if str(row.get("runtime_change_required") or "").strip() == "yes":
            runtime_required = True
    acceptance_status = "guarded_ready" if all_closed and all_green and not runtime_required else "guarded_with_residual_compat"
    return {
        "required_provider": "|".join(provider_values) if provider_values else "provider_tbd",
        "fallback_strategy": "|".join(fallback_values) if fallback_values else "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "contracts branch closure is closed; scene semantics are frozen as "
            + "|".join(menu_status_values)
            if menu_status_values
            else "contracts branch closure is closed"
        ),
        "provider_gap": "provider_registered=2;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "contracts branch closure is already closed; keep family summary synced to the dedicated contracts branch asset and observe downstream monitor follow-up scenes"
            if recommended_actions
            else "keep contracts family summary synced to the dedicated branch closure asset"
        ),
    }


def _load_payment_approval_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(PAYMENT_APPROVAL_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    row = next((item for item in rows if str(item.get("scene_key") or "").strip() == "payments.approval"), None)
    if not row:
        return {}
    acceptance_status = "guarded_ready"
    if str(row.get("closure_status") or "").strip() != "CLOSED":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("acceptance_status") or "").strip() != "all_green":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("runtime_change_required") or "").strip() == "yes":
        acceptance_status = "guarded_with_residual_compat"
    return {
        "required_provider": str(row.get("required_provider") or "").strip() or "provider_tbd",
        "fallback_strategy": str(row.get("fallback_strategy") or "").strip() or "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "payment approval branch closure is closed; scene semantics are frozen as "
            + str(row.get("menu_mapping_status") or "").strip()
        ),
        "provider_gap": "provider_registered=1;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "payment approval branch closure is already closed; keep family summary synced to the dedicated approval branch asset"
        ),
    }


def _load_payment_entry_branch_summary() -> dict[str, str]:
    rows = _read_optional_csv(PAYMENT_ENTRY_BRANCH_CLOSURE_CSV)
    if not rows:
        return {}
    row = next((item for item in rows if str(item.get("scene_key") or "").strip() == "finance.payment_requests"), None)
    if not row:
        return {}
    acceptance_status = "guarded_ready"
    if str(row.get("closure_status") or "").strip() != "CLOSED":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("acceptance_status") or "").strip() != "all_green":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("runtime_change_required") or "").strip() == "yes":
        acceptance_status = "guarded_with_residual_compat"
    return {
        "required_provider": str(row.get("required_provider") or "").strip() or "provider_tbd",
        "fallback_strategy": str(row.get("fallback_strategy") or "").strip() or "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "payment entry branch closure is closed; scene semantics are frozen as "
            + str(row.get("menu_mapping_status") or "").strip()
        ),
        "provider_gap": "provider_registered=1;fallback_only=0:none;missing=0:none",
        "planned_closure_action": (
            "payment entry branch closure is already closed; keep family summary synced to the dedicated payment-entry branch asset"
        ),
    }


def _load_enterprise_bootstrap_family_summary() -> dict[str, str]:
    rows = _read_optional_csv(ENTERPRISE_BOOTSTRAP_FAMILY_CLOSURE_CSV)
    if not rows:
        return {}
    row = rows[0]
    acceptance_status = "guarded_ready"
    if str(row.get("closure_status") or "").strip() != "CLOSED":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("acceptance_status") or "").strip() != "all_green":
        acceptance_status = "guarded_with_residual_compat"
    if str(row.get("runtime_change_required") or "").strip() == "yes":
        acceptance_status = "guarded_with_residual_compat"
    return {
        "required_provider": str(row.get("required_provider") or "").strip() or "provider_tbd",
        "fallback_strategy": str(row.get("fallback_strategy") or "").strip() or "none",
        "acceptance_status": acceptance_status,
        "menu_mapping_anomaly": (
            "enterprise bootstrap family closure is closed; family semantics are frozen as "
            + str(row.get("menu_mapping_status") or "").strip()
        ),
        "provider_gap": "provider_registered=4;fallback_only=0:none;missing=0:none",
        "planned_closure_action": "enterprise bootstrap family closure is already closed; keep family summary synced to the dedicated family closure asset",
    }


def build_rows() -> list[dict[str, str | int]]:
    authority_rows = _read_csv(AUTHORITY_CSV)
    family_rows = _read_csv(FAMILY_CSV)
    menu_rows = _read_csv(MENU_CSV)
    provider_rows = _read_csv(PROVIDER_CSV)
    score_rows = _read_csv(SCORE_CSV)
    finance_branch_summary = _load_finance_branch_summary()
    tasks_branch_summary = _load_tasks_branch_summary()
    projects_branch_summary = _load_projects_branch_summary()
    contracts_branch_summary = _load_contracts_branch_summary()
    payment_approval_branch_summary = _load_payment_approval_branch_summary()
    payment_entry_branch_summary = _load_payment_entry_branch_summary()
    enterprise_bootstrap_family_summary = _load_enterprise_bootstrap_family_summary()

    family_index = {
        str(row.get("family") or "").strip(): row
        for row in family_rows
        if str(row.get("family") or "").strip()
    }
    authority_by_family: dict[str, list[dict[str, str]]] = {}
    scene_to_family: dict[str, str] = {}
    for row in authority_rows:
        family = str(row.get("family") or "").strip()
        scene_key = str(row.get("scene_key") or "").strip()
        if not family or not scene_key:
            continue
        authority_by_family.setdefault(family, []).append(row)
        scene_to_family[scene_key] = family

    menu_by_family: dict[str, list[dict[str, str]]] = {}
    for row in menu_rows:
        scene_key = str(row.get("resolved_scene_key") or "").strip()
        family = scene_to_family.get(scene_key, "")
        if family:
            menu_by_family.setdefault(family, []).append(row)

    provider_by_family: dict[str, list[dict[str, str]]] = {}
    for row in provider_rows:
        family = scene_to_family.get(str(row.get("scene_key") or "").strip(), "")
        if family:
            provider_by_family.setdefault(family, []).append(row)

    selected_scores = sorted(
        (
            row
            for row in score_rows
            if str(row.get("family") or "").strip() in FAMILY_PLAN_MAP
        ),
        key=lambda item: (-int(str(item.get("total_score") or "0") or "0"), str(item.get("family") or "")),
    )[:TOP_FAMILY_COUNT]
    selected_family_order = [str(row.get("family") or "").strip() for row in selected_scores if str(row.get("family") or "").strip()]
    for priority_family in GOVERNED_SUMMARY_FAMILIES + ("payment_entry", "enterprise_bootstrap"):
        if priority_family in FAMILY_PLAN_MAP and priority_family not in selected_family_order:
            extra_row = next((row for row in score_rows if str(row.get("family") or "").strip() == priority_family), None)
            if extra_row:
                selected_scores.append(extra_row)
                selected_family_order.append(priority_family)

    rows: list[dict[str, str | int]] = []
    for index, score_row in enumerate(selected_scores, start=1):
        family = str(score_row.get("family") or "").strip()
        family_authority_rows = authority_by_family.get(family, [])
        if not family_authority_rows:
            raise RuntimeError(f"authority rows missing for family: {family}")
        family_authority_rows = sorted(
            family_authority_rows,
            key=lambda item: str(item.get("scene_key") or ""),
        )
        canonical_scene = str(family_index.get(family, {}).get("canonical_scene") or "").strip() or str(
            family_authority_rows[0].get("scene_key") or ""
        ).strip()
        canonical_row = next(
            (row for row in family_authority_rows if str(row.get("scene_key") or "").strip() == canonical_scene),
            family_authority_rows[0],
        )
        family_provider_rows = provider_by_family.get(family, [])
        family_menu_rows = menu_by_family.get(family, [])
        plan = FAMILY_PLAN_MAP[family]
        required_provider = _build_provider_requirement(canonical_row, family_provider_rows)
        fallback_strategy = _build_fallback_strategy(family_authority_rows)
        acceptance_status = _build_acceptance_status(family_menu_rows, family_provider_rows)
        menu_mapping_anomaly = plan["menu_mapping_anomaly"]
        provider_gap = _build_provider_gap(family_provider_rows)
        planned_closure_action = plan["planned_closure_action"]
        if family == "finance_center" and finance_branch_summary:
            required_provider = str(finance_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(finance_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(finance_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(finance_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(finance_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(finance_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "tasks" and tasks_branch_summary:
            required_provider = str(tasks_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(tasks_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(tasks_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(tasks_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(tasks_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(tasks_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "projects" and projects_branch_summary:
            required_provider = str(projects_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(projects_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(projects_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(projects_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(projects_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(projects_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "contracts" and contracts_branch_summary:
            required_provider = str(contracts_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(contracts_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(contracts_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(contracts_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(contracts_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(contracts_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "payment_approval" and payment_approval_branch_summary:
            required_provider = str(payment_approval_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(payment_approval_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(payment_approval_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(payment_approval_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(payment_approval_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(payment_approval_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "payment_entry" and payment_entry_branch_summary:
            required_provider = str(payment_entry_branch_summary.get("required_provider") or required_provider)
            fallback_strategy = str(payment_entry_branch_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(payment_entry_branch_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(payment_entry_branch_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(payment_entry_branch_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(payment_entry_branch_summary.get("planned_closure_action") or planned_closure_action)
        if family == "enterprise_bootstrap" and enterprise_bootstrap_family_summary:
            required_provider = str(enterprise_bootstrap_family_summary.get("required_provider") or required_provider)
            fallback_strategy = str(enterprise_bootstrap_family_summary.get("fallback_strategy") or fallback_strategy)
            acceptance_status = str(enterprise_bootstrap_family_summary.get("acceptance_status") or acceptance_status)
            menu_mapping_anomaly = str(enterprise_bootstrap_family_summary.get("menu_mapping_anomaly") or menu_mapping_anomaly)
            provider_gap = str(enterprise_bootstrap_family_summary.get("provider_gap") or provider_gap)
            planned_closure_action = str(enterprise_bootstrap_family_summary.get("planned_closure_action") or planned_closure_action)
        rows.append(
            {
                "priority_rank": index,
                "family": family,
                "total_score": int(str(score_row.get("total_score") or "0") or "0"),
                "user_entry": _format_entry(canonical_row),
                "final_scene": canonical_scene,
                "primary_action": _format_primary_action(canonical_row),
                "required_provider": required_provider,
                "fallback_strategy": fallback_strategy,
                "acceptance_status": acceptance_status,
                "current_authority_status": _build_authority_status(family_authority_rows),
                "canonical_entry_status": _build_canonical_status(family_authority_rows, canonical_scene),
                "menu_mapping_anomaly": menu_mapping_anomaly,
                "provider_gap": provider_gap,
                "planned_closure_action": planned_closure_action,
                "acceptance_guards": plan["acceptance_guards"],
            }
        )
    return rows


def main() -> int:
    try:
        rows = build_rows()
        _write_csv(
            OUT_CSV,
            [
                "priority_rank",
                "family",
                "total_score",
                "user_entry",
                "final_scene",
                "primary_action",
                "required_provider",
                "fallback_strategy",
                "acceptance_status",
                "current_authority_status",
                "canonical_entry_status",
                "menu_mapping_anomaly",
                "provider_gap",
                "planned_closure_action",
                "acceptance_guards",
            ],
            rows,
        )
    except Exception as exc:
        print("[scene_governance_user_flow_asset_export] FAIL")
        print(f"- {exc}")
        return 1

    print("[scene_governance_user_flow_asset_export] PASS")
    print(f"family_rows={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
