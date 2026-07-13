#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
PROJECT_LAYOUT = ROOT / "addons/smart_construction_core/core_extension_project_layout.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 4241


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    errors: list[str] = []
    core_text = _read(CORE_EXTENSION)
    layout_text = _read(PROJECT_LAYOUT)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not layout_text:
        errors.append(f"missing project layout helper: {PROJECT_LAYOUT.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_project_layout as _project_layout",
            "return _project_layout.sc_field_code(node)",
            "_project_layout.sc_set_project_label(node, field_name, label)",
            "return _project_layout.sc_prune_and_label_project_nodes(value)",
            "return _project_layout.sc_project_field_widget(",
            "return _project_layout.sc_project_field_node(",
            "return _project_layout.sc_node_has_field(value, field_name)",
            "_project_layout.sc_append_project_responsibility_group(",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing project layout split token: {token}")

    if layout_text:
        for token in [
            "def sc_text(",
            "def sc_field_code(",
            "def sc_set_project_label(",
            "def sc_prune_and_label_project_nodes(",
            "def sc_project_field_widget(",
            "def sc_project_field_node(",
            "def sc_node_has_field(",
            "def sc_append_project_responsibility_group(",
            "\"field.user_id\"",
            "\"sc_project_responsibility_collaboration\"",
            "\"项目责任与协作\"",
        ]:
            if token not in layout_text:
                errors.append(f"project layout helper missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", "requests.", "fields.", "AccessError"):
            if forbidden in layout_text:
                errors.append(f"project layout helper must remain pure projection-only; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_project_layout_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_project_layout_split_guard.py")

    if not errors:
        layout = _load(PROJECT_LAYOUT, "construction_core_extension_project_layout_under_guard")
        nodes = [
            {"type": "field", "name": "user_id", "widgetId": "field.user_id"},
            {
                "type": "field",
                "name": "manager_id",
                "fieldInfo": {},
                "componentConfig": {"relationEntry": {"ui_labels": {"dialog_title": "old"}}},
            },
        ]
        pruned = layout.sc_prune_and_label_project_nodes(nodes)
        if len(pruned) != 1 or pruned[0].get("label") != "项目经理":
            errors.append("project layout helper must remove user_id and relabel manager_id")
        dialog_title = (
            ((pruned[0].get("componentConfig") or {}).get("relationEntry") or {})
            .get("ui_labels", {})
            .get("dialog_title")
        )
        if dialog_title != "项目经理：搜索更多":
            errors.append("project layout helper must update relation-entry dialog labels")
        field_node = layout.sc_project_field_node("responsibility_ids", "项目责任分工", "one2many", relation="project.responsibility")
        if field_node.get("componentConfig", {}).get("relation") != "project.responsibility":
            errors.append("project field node must preserve relation config")
        contract = {
            "layoutContract": {"containerTree": [{"type": "group", "children": []}]},
            "statusContract": {"widgetStatus": [{"widgetId": "field.user_id"}]},
        }
        layout.sc_append_project_responsibility_group(contract, include_collaborators=True)
        tree = contract.get("layoutContract", {}).get("containerTree") or []
        group = ((tree[0] or {}).get("children") or [{}])[0]
        if group.get("name") != "sc_project_responsibility_collaboration":
            errors.append("project layout helper must append responsibility collaboration group")
        widget_ids = [row.get("widgetId") for row in (contract.get("statusContract") or {}).get("widgetStatus", [])]
        if widget_ids != ["field.responsibility_ids", "field.collaborator_ids"]:
            errors.append("project layout helper must replace user_id status and append responsibility/collaborator statuses")

    if errors:
        print("[construction_core_extension_project_layout_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_project_layout_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
