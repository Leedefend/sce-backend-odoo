# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any


def sc_text(value) -> str:
    return str(value or "").strip()


def sc_field_name(node: Any) -> str:
    if not isinstance(node, dict):
        return ""
    return sc_text(node.get("name") or node.get("field") or node.get("fieldCode"))


def sc_collect_field_nodes(nodes: Any, existing: dict[str, dict[str, Any]]) -> None:
    if isinstance(nodes, list):
        for item in nodes:
            sc_collect_field_nodes(item, existing)
        return
    if not isinstance(nodes, dict):
        return
    if sc_text(nodes.get("type")) == "field":
        name = sc_field_name(nodes)
        if name and name not in existing:
            existing[name] = deepcopy(nodes)
    for key in ("children", "widgetList", "pages", "tabs", "nodes", "items", "containerTree"):
        sc_collect_field_nodes(nodes.get(key), existing)


def sc_set_v2_container_tree(contract: dict[str, Any], container_tree: list[Any]) -> None:
    layout = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    layout["containerTree"] = container_tree
    contract["layoutContract"] = layout
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["containerTree"] = container_tree
    contract["runtimeContract"] = runtime


def sc_set_v2_widget_status(contract: dict[str, Any], widget_status: list[dict[str, Any]]) -> None:
    status = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    status["widgetStatus"] = widget_status
    contract["statusContract"] = status
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    runtime["widgetStatus"] = widget_status
    contract["runtimeContract"] = runtime


def sc_set_v2_governance_patch(contract: dict[str, Any], key: str, patch: dict[str, Any]) -> None:
    runtime = contract.get("runtimeContract") if isinstance(contract.get("runtimeContract"), dict) else {}
    patches = runtime.get("governancePatches") if isinstance(runtime.get("governancePatches"), dict) else {}
    patches[key] = patch
    runtime["governancePatches"] = patches
    contract["runtimeContract"] = runtime
    meta = contract.get("meta") if isinstance(contract.get("meta"), dict) else {}
    meta_patches = meta.get("governance_patches") if isinstance(meta.get("governance_patches"), dict) else {}
    meta_patches[key] = patch
    meta["governance_patches"] = meta_patches
    contract["meta"] = meta


def sc_replace_contract_content(contract: dict[str, Any], replacement: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not isinstance(replacement, dict):
        return
    contract.clear()
    contract.update(replacement)


def sc_form_layout_governance(source_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(source_contract, dict):
        return {}
    profile = source_contract.get("business_operation_profile")
    governance = profile.get("form_structure_governance") if isinstance(profile, dict) else {}
    return governance if isinstance(governance, dict) else {}


def sc_form_layout_columns_from_governance(governance: dict[str, Any] | None, title: str = "") -> int:
    if not isinstance(governance, dict):
        return 0
    group_columns = governance.get("group_columns") if isinstance(governance.get("group_columns"), dict) else {}
    key = sc_text(title)
    try:
        columns = int(group_columns.get(key) or 0) if key else 0
    except (TypeError, ValueError):
        columns = 0
    if columns <= 0:
        try:
            columns = int(governance.get("form_columns") or 0)
        except (TypeError, ValueError):
            columns = 0
    return columns if columns > 0 else 0


def sc_apply_form_layout_governance_to_group(
    node: dict[str, Any],
    title: str = "",
    *,
    source_contract: dict[str, Any] | None = None,
) -> None:
    if not isinstance(node, dict):
        return
    resolved_title = sc_text(title or node.get("string") or node.get("label") or node.get("title") or node.get("name"))
    columns = sc_form_layout_columns_from_governance(sc_form_layout_governance(source_contract), resolved_title)
    if columns <= 0:
        return
    node["cols"] = columns
    node["columns"] = columns
    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
    attrs["col"] = str(columns)
    node["attributes"] = attrs
