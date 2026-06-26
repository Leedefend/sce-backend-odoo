#!/usr/bin/env python3
"""Guard UiContractV2 handler/assembler contract ownership boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
ASSEMBLER = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"

ALLOWED_FINAL_CONTRACT_MUTATORS = {
    "_normalize_general_contract_tax_contract",
    "_apply_business_config_form_groups_to_v2",
    "_normalize_general_contract_company_form",
    "_normalize_construction_diary_form",
    "_apply_legacy_visible_list_layout",
    "_apply_field_policies_to_v2_status",
    "_ensure_native_layout_widget_status_visible",
    "_sync_contract_original_contract_relation_to_v2_nodes",
}

ALLOWED_SOURCE_PROJECTION_WRITERS = {
    "_inject_business_category_form_structure",
    "_inject_business_operation_contract",
    "_inject_collaboration_contract",
    "_inject_standard_submit_header_button",
    "_inject_record_business_category_context",
}

FINAL_CONTRACT_KEYS = {
    "layoutContract",
    "statusContract",
    "containerTree",
    "widgetStatus",
    "containerStatus",
    "buttonStatus",
}

SOURCE_PROJECTION_KEYS = {
    "form_structure_contract",
    "business_operation_profile",
    "collaboration",
    "header_buttons",
}

FORBIDDEN_SOURCE_VIEW_KEYS = {
    "views",
    "form",
}


def _constant_key(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def _subscript_keys(node: ast.AST) -> list[str]:
    keys: list[str] = []
    current = node
    while isinstance(current, ast.Subscript):
        key = _constant_key(current.slice)
        if key:
            keys.append(key)
        current = current.value
    keys.reverse()
    return keys


def _assigned_keys(node: ast.AST) -> set[str]:
    out: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Subscript):
            out.update(_subscript_keys(child))
    return out


def _function_for(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
    return "<module>"


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _assignment_nodes(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            nodes.extend(node.targets)
        elif isinstance(node, ast.AnnAssign):
            nodes.append(node.target)
        elif isinstance(node, ast.AugAssign):
            nodes.append(node.target)
    return nodes


def main() -> int:
    source = HANDLER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    parents = _parent_map(tree)
    violations: list[str] = []

    for target in _assignment_nodes(tree):
        keys = _assigned_keys(target)
        if not keys:
            continue
        function = _function_for(target, parents)
        line = getattr(target, "lineno", 0)

        if FINAL_CONTRACT_KEYS & keys and function not in ALLOWED_FINAL_CONTRACT_MUTATORS:
            violations.append(
                f"{HANDLER.relative_to(ROOT)}:{line}: {function} writes final V2 contract keys "
                f"{sorted(FINAL_CONTRACT_KEYS & keys)} without allowlist"
            )

        if SOURCE_PROJECTION_KEYS & keys and function not in ALLOWED_SOURCE_PROJECTION_WRITERS:
            violations.append(
                f"{HANDLER.relative_to(ROOT)}:{line}: {function} writes source projection keys "
                f"{sorted(SOURCE_PROJECTION_KEYS & keys)} without allowlist"
            )

        if FORBIDDEN_SOURCE_VIEW_KEYS.issubset(keys):
            violations.append(
                f"{HANDLER.relative_to(ROOT)}:{line}: {function} mutates source_contract.views.form; "
                "handler must emit source projections and let assembler own final layout"
            )

    assembler_source = ASSEMBLER.read_text(encoding="utf-8")
    if "source.get(\"header_buttons\")" not in assembler_source:
        violations.append(
            f"{ASSEMBLER.relative_to(ROOT)}: assembler must consume top-level source.header_buttons "
            "instead of requiring handlers to mutate views.form.header_buttons"
        )

    if violations:
        print("[ui_contract_v2_contract_boundary_guard] FAIL")
        for item in violations:
            print(item)
        return 1

    print("[ui_contract_v2_contract_boundary_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
