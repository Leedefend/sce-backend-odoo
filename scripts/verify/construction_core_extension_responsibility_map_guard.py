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
        "Current size: 4,180 lines",
        "staged responsibility split",
        "## Public Entry Points",
        "## Responsibility Bands",
        "## Current Guards",
        "## Stage 1 Target",
        "## Stage 2 Target",
        "`core_extension_project_layout.py` owns pure project form layout helpers",
        "`core_extension_contract_helpers.py` owns generic contract helper utilities",
        "`core_extension.py` is locked at `<=4180` lines",
        "Do not move import-time registration side effects",
        "projection-only",
    ]:
        if token not in doc:
            errors.append(f"responsibility map missing token: {token}")

    for guard in [
        "construction_core_extension_project_layout_split_guard.py",
        "construction_core_extension_contract_helpers_split_guard.py",
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

    split_queue_token = (
        "`addons/smart_construction_core/core_extension.py` | "
        "Define owner-specific decomposition plan before adding unrelated behavior."
    )
    if split_queue_token not in split_queue:
        errors.append("split plan queue must keep core_extension decomposition direction")

    for ci_token in [
        "python3 scripts/verify/construction_core_extension_project_layout_split_guard.py",
        "python3 scripts/verify/construction_core_extension_contract_helpers_split_guard.py",
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
