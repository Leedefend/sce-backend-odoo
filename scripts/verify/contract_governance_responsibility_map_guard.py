#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/engineering_convergence/contract_governance_responsibility_map.md"
GOVERNANCE = ROOT / "addons/smart_core/utils/contract_governance.py"
SPLIT_QUEUE = ROOT / "docs/engineering_convergence/split_plan_queue.md"
CI = ROOT / "make/ci.mk"

PUBLIC_ENTRY_POINTS = [
    "apply_contract_governance",
    "resolve_contract_mode",
    "resolve_contract_surface",
    "normalize_capabilities",
    "normalize_scenes",
    "register_legacy_standard_list_profile",
    "register_contract_domain_override",
]

RESPONSIBILITY_BANDS = [
    "Constants and registries",
    "Source authority and registry API",
    "User surface normalization",
    "Project and enterprise governance",
    "Standard list governance",
    "Native surface and scene bridge",
    "Form policy and render semantics",
    "Domain override and diagnostics",
    "Main pipeline",
]

REQUIRED_GUARDS = [
    "contract_governance_determinism_guard.py",
    "contract_governance_coverage.py",
    "contract_governance_brief.py",
    "test_contract_governance_project_form.py",
    "test_contract_governance_record_context_registry.py",
    "test_contract_governance_kanban_profile_registry.py",
    "test_contract_governance_task_form_profile_registry.py",
    "test_odoo_native_alignment_boundaries.py",
    "list_batch_action_closure_guard.py",
    "contract_governance_registry_split_guard.py",
    "contract_governance_user_surface_split_guard.py",
    "contract_governance_capabilities_split_guard.py",
    "contract_governance_scenes_split_guard.py",
    "contract_governance_list_surface_split_guard.py",
    "contract_governance_native_bridge_split_guard.py",
    "contract_governance_labels_split_guard.py",
    "contract_governance_access_policy_split_guard.py",
    "contract_governance_canonicalization_split_guard.py",
    "contract_governance_surface_mapping_split_guard.py",
    "contract_governance_create_profile_split_guard.py",
    "contract_governance_field_semantics_split_guard.py",
    "contract_governance_form_layout_split_guard.py",
    "contract_governance_form_actions_split_guard.py",
    "contract_governance_form_render_split_guard.py",
    "contract_governance_form_validation_split_guard.py",
    "contract_governance_form_fields_split_guard.py",
    "contract_governance_project_form_split_guard.py",
]

INVARIANTS = [
    "No ORM calls, HTTP calls, routing, file IO, or environment access",
    "must not invent backend permission truth",
    "Native surface must keep parser-origin structure",
    "User mode must strip diagnostic/internal fields",
    "HUD mode may emit diagnostics",
    "Surface mapping must compare native and governed snapshots",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    governance = _read(GOVERNANCE)
    split_queue = _read(SPLIT_QUEUE)
    ci = _read(CI)

    if not doc:
        errors.append(f"missing responsibility map: {DOC.relative_to(ROOT)}")
    if not governance:
        errors.append(f"missing contract governance file: {GOVERNANCE.relative_to(ROOT)}")

    for token in [
        "Contract Governance Responsibility Map",
        "Current size: 2,708 lines",
        "projection-only",
        "Do not start mechanical extraction",
        "## Public Entry Points",
        "## Responsibility Bands",
        "## Current Guards",
        "## Extraction Order",
        "## Do Not Move Yet",
        "## Invariants",
        "## Next Implementation Candidate",
        "## Stage 1 Target",
        "`contract_governance_registry.py` owns source authority constants",
        "`contract_governance.py` is locked at `<=4655` lines",
        "## Stage 2 Target",
        "`contract_governance_user_surface.py` owns recursive user-mode field stripping",
        "`contract_governance.py` is locked at `<=4535` lines",
        "## Stage 3 Target",
        "`contract_governance_registry.py` also owns form policy constants",
        "`contract_governance.py` is locked at `<=4490` lines",
        "## Stage 4 Target",
        "`contract_governance_capabilities.py` owns capability normalization",
        "`contract_governance.py` is locked at `<=4272` lines",
        "## Stage 5 Target",
        "`contract_governance_scenes.py` owns scene normalization",
        "`contract_governance.py` is locked at `<=4213` lines",
        "## Stage 6 Target",
        "`contract_governance_list_surface.py` owns standard list toolbar labels",
        "`contract_governance.py` is locked at `<=4121` lines",
        "## Stage 7 Target",
        "`contract_governance_native_bridge.py` owns native and scene bridge normalization",
        "`contract_governance.py` is locked at `<=3932` lines",
        "## Stage 8 Target",
        "`contract_governance_labels.py` owns business labels and relation semantics",
        "`contract_governance.py` is locked at `<=3830` lines",
        "## Stage 9 Target",
        "`contract_governance_access_policy.py` owns access policy realignment",
        "`contract_governance.py` is locked at `<=3780` lines",
        "## Stage 10 Target",
        "`contract_governance_canonicalization.py` owns recursive contract key",
        "`contract_governance.py` is locked at `<=3769` lines",
        "## Stage 11 Target",
        "`contract_governance_surface_mapping.py` owns surface snapshot collection",
        "`contract_governance.py` is locked at `<=3690` lines",
        "## Stage 12 Target",
        "`contract_governance_create_profile.py` owns create-profile projection cleanup",
        "`contract_governance.py` is locked at `<=3528` lines",
        "## Stage 13 Target",
        "`contract_governance_field_semantics.py` owns field technical classification",
        "`contract_governance.py` is locked at `<=3453` lines",
        "## Stage 14 Target",
        "`contract_governance_form_layout.py` owns form layout structural helpers",
        "`contract_governance.py` is locked at `<=3361` lines",
        "## Stage 15 Target",
        "`contract_governance_form_actions.py` owns form action semantic inference",
        "`contract_governance.py` is locked at `<=3212` lines",
        "## Stage 16 Target",
        "`contract_governance_form_render.py` owns boolean coercion",
        "`contract_governance.py` is locked at `<=3169` lines",
        "## Stage 17 Target",
        "`contract_governance_form_validation.py` owns validation rule assembly",
        "`contract_governance.py` is locked at `<=3073` lines",
        "## Stage 18 Target",
        "`contract_governance_form_fields.py` owns form field ordering",
        "`contract_governance.py` is locked at `<=2930` lines",
        "## Stage 19 Target",
        "`contract_governance_list_surface.py` also owns tier-review list",
        "`contract_governance.py` is locked at `<=2898` lines",
        "## Stage 20 Target",
        "`contract_governance_project_form.py` owns project lifecycle summary",
        "`contract_governance.py` is locked at `<=2872` lines",
        "## Stage 21 Target",
        "`contract_governance_project_form.py` also owns legacy project form profile",
        "`contract_governance.py` is locked at `<=2781` lines",
        "## Stage 22 Target",
        "`contract_governance_project_form.py` also owns project form layout filtering",
        "`contract_governance.py` is locked at `<=2708` lines",
    ]:
        if token not in doc:
            errors.append(f"responsibility map missing token: {token}")

    for entry in PUBLIC_ENTRY_POINTS:
        if f"`{entry}" not in doc:
            errors.append(f"responsibility map missing public entry: {entry}")

    for band in RESPONSIBILITY_BANDS:
        if band not in doc:
            errors.append(f"responsibility map missing band: {band}")

    for guard in REQUIRED_GUARDS:
        if guard not in doc:
            errors.append(f"responsibility map missing guard: {guard}")

    for invariant in INVARIANTS:
        if invariant not in doc:
            errors.append(f"responsibility map missing invariant: {invariant}")

    if governance:
        functions = _function_names(governance)
        for entry in PUBLIC_ENTRY_POINTS:
            if entry not in functions:
                errors.append(f"contract_governance.py missing public entry: {entry}")
        if "data[\"contract_surface\"] = normalized_surface" not in governance:
            errors.append("apply_contract_governance must still emit contract_surface")
        if "data[\"surface_mapping\"] = surface_mapping" not in governance:
            errors.append("apply_contract_governance must still emit surface_mapping")
        if "if normalized_surface == \"native\":" not in governance:
            errors.append("apply_contract_governance must retain native surface branch")

    split_queue_token = (
        "`addons/smart_core/utils/contract_governance.py` | Extract constants/registries, "
        "user-surface normalization, list governance, native bridge, form policy, diagnostics, "
        "and keep `apply_contract_governance` as a thin facade."
    )
    if split_queue_token not in split_queue:
        errors.append("split plan queue must use contract_governance-specific decomposition direction")

    ci_token = "python3 scripts/verify/contract_governance_responsibility_map_guard.py"
    if ci_token not in ci:
        errors.append("ci.local.quick must run contract_governance_responsibility_map_guard.py")

    if errors:
        print("[contract_governance_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[contract_governance_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
