#!/usr/bin/env python3
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/engineering_convergence/construction_core_extension_responsibility_map.md"
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
SPLIT_QUEUE = ROOT / "docs/engineering_convergence/split_plan_queue.md"
CI = ROOT / "make/ci.mk"

PUBLIC_ENTRY_POINTS = [
    "smart_core_finalize_unified_page_contract_v2",
    "smart_core_normalize_projected_contract_data",
    "smart_core_normalize_unified_page_contract_v2",
    "get_capability_contributions",
    "get_system_init_fact_contributions",
    "smart_core_extend_system_init",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _function_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main() -> int:
    errors: list[str] = []
    doc = _read(DOC)
    core = _read(CORE_EXTENSION)
    split_queue = _read(SPLIT_QUEUE)
    ci = _read(CI)

    if not doc:
        errors.append(f"missing responsibility map: {DOC.relative_to(ROOT)}")
    if not core:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")

    for token in [
        "Construction Core Extension Responsibility Map",
        "Current size: 1,858 lines",
        "staged responsibility split",
        "## Public Entry Points",
        "## Responsibility Bands",
        "## Current Guards",
        "## Stage 1 Target",
        "## Stage 2 Target",
        "## Stage 3 Target",
        "## Stage 4 Target",
        "## Stage 5 Target",
        "## Stage 6 Target",
        "## Stage 7 Target",
        "## Stage 8 Target",
        "## Stage 9 Target",
        "## Stage 10 Target",
        "## Stage 11 Target",
        "## Stage 12 Target",
        "`core_extension_project_layout.py` owns pure project form layout helpers",
        "`core_extension_contract_helpers.py` owns generic contract helper utilities",
        "`core_extension_policy_maps.py` owns static construction policy/map facts",
        "`core_extension_system_init_rows.py` owns read-side system-init row builders",
        "`core_extension_capability_rows.py` owns capability row normalization",
        "`core_extension_hook_facts.py` owns static hook facts",
        "`core_extension_policy_accessors.py` owns read-side policy accessors",
        "`core_extension_contract_normalizers.py` owns projection-only contract",
        "`core_extension_intent_handlers.py` owns lazy construction intent handler",
        "`core_extension_hook_facts.py` also owns static menu delivery token policy",
        "`core_extension_service_builders.py` owns lazy service class and service",
        "`core_extension_system_init_rows.py` also owns system-init workspace and page",
        "`core_extension.py` is locked at `<=1858` lines",
        "Do not move import-time registration side effects",
        "workflow projection reads `env`, registry, records",
        "`smart_core_register(registry)` because registry writes",
        "projection-only",
    ]:
        if token not in doc:
            errors.append(f"responsibility map missing token: {token}")

    for guard in [
        "construction_core_extension_project_layout_split_guard.py",
        "construction_core_extension_contract_helpers_split_guard.py",
        "construction_core_extension_policy_maps_split_guard.py",
        "construction_core_extension_system_init_rows_split_guard.py",
        "construction_core_extension_capability_rows_split_guard.py",
        "construction_core_extension_hook_facts_split_guard.py",
        "construction_core_extension_policy_accessors_split_guard.py",
        "construction_core_extension_contract_normalizers_split_guard.py",
        "construction_core_extension_intent_handlers_split_guard.py",
        "construction_core_extension_service_builders_split_guard.py",
        "backend_boundary_guard.py",
        "owner_industry_isolation_probe.py",
    ]:
        if guard not in doc:
            errors.append(f"responsibility map missing guard: {guard}")

    if core:
        functions = _function_names(core)
        for entry in PUBLIC_ENTRY_POINTS:
            if entry not in functions:
                errors.append(f"core_extension.py missing public entry: {entry}")
        if "core_extension_project_layout as _project_layout" not in core:
            errors.append("core_extension.py must import project layout helper module")
        if "_project_layout.sc_append_project_responsibility_group(" not in core:
            errors.append("core_extension.py must delegate project responsibility group helper")
        if "core_extension_contract_helpers as _contract_helpers" not in core:
            errors.append("core_extension.py must import contract helper module")
        if "_contract_helpers.sc_set_v2_container_tree(contract, container_tree)" not in core:
            errors.append("core_extension.py must delegate contract container tree helper")
        if "core_extension_policy_maps as _policy_maps" not in core:
            errors.append("core_extension.py must import policy maps module")
        if "ROLE_SURFACE_OVERRIDES = _policy_maps.ROLE_SURFACE_OVERRIDES" not in core:
            errors.append("core_extension.py must delegate role surface maps")
        if "register_legacy_standard_list_profile({" not in core:
            errors.append("core_extension.py must keep import-time list profile registration")
        if "core_extension_system_init_rows as _system_init_rows" not in core:
            errors.append("core_extension.py must import system init rows module")
        if "return _system_init_rows.build_task_action_rows(env, user)" not in core:
            errors.append("core_extension.py must delegate task action row builder")
        if "return _system_init_rows.build_home_block_contract_rows(env)" not in core:
            errors.append("core_extension.py must delegate home block row builder")
        if "return _system_init_rows.apply_system_init_profile_overrides(data)" not in core:
            errors.append("core_extension.py must delegate system-init profile overrides")
        if "core_extension_capability_rows as _capability_rows" not in core:
            errors.append("core_extension.py must import capability rows module")
        if "return _capability_rows.normalize_capability_rows(capabilities)" not in core:
            errors.append("core_extension.py must delegate capability rows")
        if "core_extension_hook_facts as _hook_facts" not in core:
            errors.append("core_extension.py must import hook facts module")
        if "return _hook_facts.scene_entry_orchestrator_specs()" not in core:
            errors.append("core_extension.py must delegate scene orchestrator specs")
        if "return _hook_facts.menu_delivery_token_policy()" not in core:
            errors.append("core_extension.py must delegate menu delivery token policy")
        if "core_extension_policy_accessors as _policy_accessors" not in core:
            errors.append("core_extension.py must import policy accessors module")
        if "return _policy_accessors.get_api_data_unlink_allowed_model_contributions(env)" not in core:
            errors.append("core_extension.py must delegate unlink policy accessors")
        if "core_extension_contract_normalizers as _contract_normalizers" not in core:
            errors.append("core_extension.py must import contract normalizers module")
        if "_contract_normalizers.normalize_construction_diary_form(contract, source_contract, model=model, view_type=view_type)" not in core:
            errors.append("core_extension.py must delegate construction diary normalizer")
        if "_contract_normalizers.general_contract_tax_contract(contract, source_contract=source_contract)" not in core:
            errors.append("core_extension.py must delegate general contract tax normalizer")
        if "_contract_normalizers.normalize_general_contract_company_form(contract, source_contract=source_contract)" not in core:
            errors.append("core_extension.py must delegate general contract company normalizer")
        if "def _sc_inject_workflow_contract(env, contract, source, *, model, view_type):" not in core:
            errors.append("core_extension.py must keep workflow injection boundary in facade")
        if "core_extension_intent_handlers as _intent_handlers" not in core:
            errors.append("core_extension.py must import intent handlers module")
        if "return _intent_handlers.get_intent_handler_contributions()" not in core:
            errors.append("core_extension.py must delegate intent handler contributions")
        if "core_extension_service_builders as _service_builders" not in core:
            errors.append("core_extension.py must import service builders module")
        if "return _service_builders.build_project_execution_service(env)" not in core:
            errors.append("core_extension.py must delegate service builders")
        if "return _service_builders.build_settlement_slice_service(env)" not in core:
            errors.append("core_extension.py must delegate settlement service builder")
        if "def smart_core_register(registry):" not in core or "registry[intent_name] = handler" not in core:
            errors.append("core_extension.py must keep registry write boundary in facade")
        if "APPROVAL_POLICY_INTENTS" in core:
            errors.append("core_extension.py must not keep approval policy intent constants after handler extraction")

    split_queue_token = (
        "`addons/smart_construction_core/core_extension.py` | "
        "Define owner-specific decomposition plan before adding unrelated behavior."
    )
    if split_queue_token not in split_queue:
        errors.append("split plan queue must keep core_extension decomposition direction")

    for ci_token in [
        "python3 scripts/verify/construction_core_extension_project_layout_split_guard.py",
        "python3 scripts/verify/construction_core_extension_contract_helpers_split_guard.py",
        "python3 scripts/verify/construction_core_extension_policy_maps_split_guard.py",
        "python3 scripts/verify/construction_core_extension_system_init_rows_split_guard.py",
        "python3 scripts/verify/construction_core_extension_capability_rows_split_guard.py",
        "python3 scripts/verify/construction_core_extension_hook_facts_split_guard.py",
        "python3 scripts/verify/construction_core_extension_policy_accessors_split_guard.py",
        "python3 scripts/verify/construction_core_extension_contract_normalizers_split_guard.py",
        "python3 scripts/verify/construction_core_extension_intent_handlers_split_guard.py",
        "python3 scripts/verify/construction_core_extension_service_builders_split_guard.py",
        "python3 scripts/verify/construction_core_extension_responsibility_map_guard.py",
    ]:
        if ci_token not in ci:
            errors.append(f"ci.local.quick must run {ci_token}")

    if errors:
        print("[construction_core_extension_responsibility_map_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_responsibility_map_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
