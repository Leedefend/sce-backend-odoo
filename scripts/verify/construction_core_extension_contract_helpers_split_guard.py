#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE_EXTENSION = ROOT / "addons/smart_construction_core/core_extension.py"
HELPERS = ROOT / "addons/smart_construction_core/core_extension_contract_helpers.py"
CI = ROOT / "make/ci.mk"

MAX_CORE_EXTENSION_LINES = 4180


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
    helper_text = _read(HELPERS)
    ci_text = _read(CI)

    if not core_text:
        errors.append(f"missing core extension file: {CORE_EXTENSION.relative_to(ROOT)}")
    if not helper_text:
        errors.append(f"missing contract helper module: {HELPERS.relative_to(ROOT)}")

    if core_text:
        line_count = len(core_text.splitlines())
        if line_count > MAX_CORE_EXTENSION_LINES:
            errors.append(f"core_extension.py line budget exceeded: {line_count} > {MAX_CORE_EXTENSION_LINES}")
        for token in [
            "core_extension_contract_helpers as _contract_helpers",
            "return _contract_helpers.sc_field_name(node)",
            "_contract_helpers.sc_collect_field_nodes(nodes, existing)",
            "_contract_helpers.sc_set_v2_container_tree(contract, container_tree)",
            "_contract_helpers.sc_set_v2_widget_status(contract, widget_status)",
            "_contract_helpers.sc_set_v2_governance_patch(contract, key, patch)",
            "_contract_helpers.sc_replace_contract_content(contract, replacement)",
            "return _contract_helpers.sc_form_layout_governance(source_contract)",
            "return _contract_helpers.sc_form_layout_columns_from_governance(governance, title)",
            "_contract_helpers.sc_apply_form_layout_governance_to_group(",
        ]:
            if token not in core_text:
                errors.append(f"core_extension.py missing contract helper split token: {token}")

    if helper_text:
        for token in [
            "def sc_field_name(",
            "def sc_collect_field_nodes(",
            "def sc_set_v2_container_tree(",
            "def sc_set_v2_widget_status(",
            "def sc_set_v2_governance_patch(",
            "def sc_replace_contract_content(",
            "def sc_form_layout_governance(",
            "def sc_form_layout_columns_from_governance(",
            "def sc_apply_form_layout_governance_to_group(",
        ]:
            if token not in helper_text:
                errors.append(f"contract helper module missing token: {token}")
        for forbidden in ("env[", ".search(", ".write(", "requests.", "fields.", "AccessError"):
            if forbidden in helper_text:
                errors.append(f"contract helper module must remain projection-only; forbidden token: {forbidden}")

    if "python3 scripts/verify/construction_core_extension_contract_helpers_split_guard.py" not in ci_text:
        errors.append("ci.local.quick must run construction_core_extension_contract_helpers_split_guard.py")

    if not errors:
        helpers = _load(HELPERS, "construction_core_extension_contract_helpers_under_guard")
        existing: dict[str, dict] = {}
        node = {"type": "field", "name": "amount_total", "children": [{"type": "field", "fieldCode": "tax_id"}]}
        helpers.sc_collect_field_nodes([node], existing)
        if sorted(existing) != ["amount_total", "tax_id"]:
            errors.append("contract helper must collect nested field nodes")
        contract: dict = {}
        tree = [{"type": "group"}]
        helpers.sc_set_v2_container_tree(contract, tree)
        if contract.get("layoutContract", {}).get("containerTree") is not tree:
            errors.append("contract helper must write layoutContract containerTree")
        if contract.get("runtimeContract", {}).get("containerTree") is not tree:
            errors.append("contract helper must mirror containerTree into runtimeContract")
        widget_status = [{"widgetId": "field.name", "visible": True}]
        helpers.sc_set_v2_widget_status(contract, widget_status)
        if contract.get("runtimeContract", {}).get("widgetStatus") != widget_status:
            errors.append("contract helper must mirror widgetStatus into runtimeContract")
        helpers.sc_set_v2_governance_patch(contract, "sample", {"applied": True})
        if contract.get("meta", {}).get("governance_patches", {}).get("sample") != {"applied": True}:
            errors.append("contract helper must mirror governance patches into meta")
        source_contract = {"business_operation_profile": {"form_structure_governance": {"form_columns": 2, "group_columns": {"金额": 3}}}}
        if helpers.sc_form_layout_columns_from_governance(helpers.sc_form_layout_governance(source_contract), "金额") != 3:
            errors.append("contract helper must prefer group-specific layout columns")
        group = {"name": "amount"}
        helpers.sc_apply_form_layout_governance_to_group(group, "金额", source_contract=source_contract)
        if group.get("cols") != 3 or group.get("attributes", {}).get("col") != "3":
            errors.append("contract helper must apply group layout governance attributes")
        helpers.sc_replace_contract_content(contract, {"replacement": True})
        if contract != {"replacement": True}:
            errors.append("contract helper must replace contract content in place")

    if errors:
        print("[construction_core_extension_contract_helpers_split_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[construction_core_extension_contract_helpers_split_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
