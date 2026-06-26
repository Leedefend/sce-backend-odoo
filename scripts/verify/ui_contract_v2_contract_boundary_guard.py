#!/usr/bin/env python3
"""Guard UiContractV2 handler/assembler contract ownership boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HANDLER = ROOT / "addons/smart_core/handlers/ui_contract_v2.py"
ASSEMBLER = ROOT / "addons/smart_core/core/unified_page_contract_v2_assembler.py"

ALLOWED_FINAL_CONTRACT_WRITERS = {
    "_set_v2_container_tree",
    "_set_v2_widget_status",
    "_set_v2_data_meta",
    "_replace_v2_contract_content",
    "_set_v2_governance_patch",
    "_copy_v2_source_passthroughs",
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
    "dataContract",
    "dataMeta",
    "governance",
    "delete_policy",
    "surface_policies",
    "list_profile",
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


def _subscript_root(node: ast.AST) -> str:
    current = node
    while isinstance(current, ast.Subscript):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return ""


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


def _contract_replacement_calls(tree: ast.AST) -> list[ast.Call]:
    out: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"clear", "update"}:
            continue
        value = node.func.value
        if isinstance(value, ast.Name) and value.id in {"contract", "contract_v2"}:
            out.append(node)
    return out


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
        root = _subscript_root(target)

        if root in {"contract", "contract_v2"} and FINAL_CONTRACT_KEYS & keys and function not in ALLOWED_FINAL_CONTRACT_WRITERS:
            violations.append(
                f"{HANDLER.relative_to(ROOT)}:{line}: {function} writes final V2 contract keys "
                f"{sorted(FINAL_CONTRACT_KEYS & keys)} outside centralized V2 contract patch helpers"
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

    for call in _contract_replacement_calls(tree):
        function = _function_for(call, parents)
        line = getattr(call, "lineno", 0)
        if function != "_replace_v2_contract_content":
            violations.append(
                f"{HANDLER.relative_to(ROOT)}:{line}: {function} directly calls contract.{call.func.attr}(); "
                "whole-contract replacement must go through _replace_v2_contract_content"
            )

    assembler_source = ASSEMBLER.read_text(encoding="utf-8")
    if "source.get(\"header_buttons\")" not in assembler_source:
        violations.append(
            f"{ASSEMBLER.relative_to(ROOT)}: assembler must consume top-level source.header_buttons "
            "instead of requiring handlers to mutate views.form.header_buttons"
        )
    if "def _data_source_authority(" not in assembler_source or "\"sourceAuthority\": source_authority" not in assembler_source:
        violations.append(
            f"{ASSEMBLER.relative_to(ROOT)}: dataContract.dataSource rows must be stamped with _data_source_authority"
        )
    if "def _compat_projection_source_authority(" not in assembler_source or "compat_projection[\"sourceAuthority\"] = _compat_projection_source_authority()" not in assembler_source:
        violations.append(
            f"{ASSEMBLER.relative_to(ROOT)}: legacyContractProjection must carry compatibility sourceAuthority"
        )
    runtime_path = ROOT / "addons/smart_core/core/unified_page_contract_v2_runtime.py"
    runtime_source = runtime_path.read_text(encoding="utf-8")
    if "def find_data_source_authority_issues(" not in runtime_source or "issues.extend(find_data_source_authority_issues(data))" not in runtime_source:
        violations.append(
            f"{runtime_path.relative_to(ROOT)}: runtime guard must validate dataSource and legacy projection authority"
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
