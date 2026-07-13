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
        "Current size: 4,820 lines",
        "projection-only",
        "Do not start mechanical extraction",
        "## Public Entry Points",
        "## Responsibility Bands",
        "## Current Guards",
        "## Extraction Order",
        "## Do Not Move Yet",
        "## Invariants",
        "## Next Implementation Candidate",
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
