# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import ui_contract_v2_adapters as _adapters


def set_v2_container_tree(contract: dict[str, Any], container_tree: list[Any]) -> None:
    if not isinstance(contract, dict):
        return
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    layout_contract["containerTree"] = container_tree
    contract["layoutContract"] = layout_contract


def set_v2_widget_status(contract: dict[str, Any], widget_status: list[dict[str, Any]]) -> None:
    if not isinstance(contract, dict):
        return
    status_contract = contract.get("statusContract") if isinstance(contract.get("statusContract"), dict) else {}
    status_contract["widgetStatus"] = widget_status
    contract["statusContract"] = status_contract


def set_v2_data_meta(contract: dict[str, Any], patch: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not isinstance(patch, dict):
        return
    data_contract = contract.get("dataContract") if isinstance(contract.get("dataContract"), dict) else {}
    data_meta = data_contract.get("dataMeta") if isinstance(data_contract.get("dataMeta"), dict) else {}
    data_meta.update(patch)
    data_contract["dataMeta"] = data_meta
    contract["dataContract"] = data_contract


def replace_v2_contract_content(contract: dict[str, Any], replacement: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not isinstance(replacement, dict):
        return
    contract.clear()
    contract.update(replacement)


def set_v2_governance_patch(contract: dict[str, Any], key: str, patch: dict[str, Any]) -> None:
    if not isinstance(contract, dict) or not key or not isinstance(patch, dict):
        return
    governance = contract.get("governance") if isinstance(contract.get("governance"), dict) else {}
    governance[key] = patch
    contract["governance"] = governance


def project_v2_source_policies(
    contract: dict[str, Any],
    source_contract: dict[str, Any],
    *,
    source_kind: str,
    no_business_fact_authority: bool,
) -> None:
    if not isinstance(contract, dict) or not isinstance(source_contract, dict):
        return
    if isinstance(source_contract.get("delete_policy"), dict):
        delete_policy = dict(source_contract.get("delete_policy") or {})
        action_contract = contract.get("actionContract") if isinstance(contract.get("actionContract"), dict) else {}
        action_contract["deletePolicy"] = _adapters.v2_policy_projection(
            delete_policy,
            source_kind=source_kind,
            no_business_fact_authority=no_business_fact_authority,
            runtime_carrier="ui.contract.v2.actionContract.deletePolicy",
            source_key="delete_policy",
        )
        contract["actionContract"] = action_contract
    if isinstance(source_contract.get("surface_policies"), dict):
        surface_policies = deepcopy(source_contract.get("surface_policies") or {})
        action_contract = contract.get("actionContract") if isinstance(contract.get("actionContract"), dict) else {}
        action_contract["surfacePolicies"] = _adapters.v2_policy_projection(
            surface_policies,
            source_kind=source_kind,
            no_business_fact_authority=no_business_fact_authority,
            runtime_carrier="ui.contract.v2.actionContract.surfacePolicies",
            source_key="surface_policies",
        )
        contract["actionContract"] = action_contract
    if isinstance(source_contract.get("list_profile"), dict):
        list_profile = deepcopy(source_contract.get("list_profile") or {})
        layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
        layout_contract["listProfile"] = _adapters.v2_policy_projection(
            list_profile,
            source_kind=source_kind,
            no_business_fact_authority=no_business_fact_authority,
            runtime_carrier="ui.contract.v2.layoutContract.listProfile",
            source_key="list_profile",
        )
        contract["layoutContract"] = layout_contract


def apply_field_policies_to_v2_status(contract_v2: dict[str, Any], source_contract: dict[str, Any]) -> None:
    field_policies = source_contract.get("field_policies") if isinstance(source_contract.get("field_policies"), dict) else {}
    if not field_policies:
        return
    business_policy = source_contract.get("business_form_policy") if isinstance(source_contract.get("business_form_policy"), dict) else {}
    render_profile = str(
        source_contract.get("render_profile")
        or business_policy.get("render_profile")
        or ""
    ).strip().lower()
    if render_profile in {"read", "view"}:
        render_profile = "readonly"
    if render_profile not in {"create", "edit", "readonly"}:
        render_profile = "edit"
    status_contract = contract_v2.get("statusContract") if isinstance(contract_v2.get("statusContract"), dict) else {}
    widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
    by_widget: dict[str, list[dict[str, Any]]] = {}
    for row in widget_status:
        if not isinstance(row, dict):
            continue
        widget_id = str(row.get("widgetId") or "").strip()
        if widget_id:
            by_widget.setdefault(widget_id, []).append(row)

    def apply_policy(row: dict[str, Any], policy: dict[str, Any]) -> None:
        visible_profiles = policy.get("visible_profiles")
        if isinstance(visible_profiles, list) and visible_profiles:
            row["visible"] = render_profile in {str(item) for item in visible_profiles}
        readonly_profiles = policy.get("readonly_profiles")
        if isinstance(readonly_profiles, list) and readonly_profiles:
            row["readonly"] = render_profile in {str(item) for item in readonly_profiles}
        required_profiles = policy.get("required_profiles")
        if isinstance(required_profiles, list) and required_profiles:
            row["required"] = render_profile in {str(item) for item in required_profiles}
        for key in ("visible", "readonly", "required", "disabled"):
            if isinstance(policy.get(key), bool):
                row[key] = bool(policy.get(key))
        row["auth"] = "none" if row.get("visible") is False else "read" if row.get("readonly") else "edit"

    for field_name, policy in field_policies.items():
        if not isinstance(policy, dict):
            continue
        field_code = str(field_name or "").strip()
        if not field_code:
            continue
        widget_id = f"field.{field_code}"
        rows = by_widget.get(widget_id)
        if not rows:
            row = {
                "widgetId": widget_id,
                "visible": True,
                "readonly": False,
                "required": False,
                "disabled": False,
                "auth": "edit",
            }
            widget_status.append(row)
            rows = [row]
        for row in rows:
            apply_policy(row, policy)
    set_v2_widget_status(contract_v2, widget_status)


def ensure_native_layout_widget_status_visible(contract_v2: dict[str, Any]) -> None:
    layout_contract = contract_v2.get("layoutContract") if isinstance(contract_v2.get("layoutContract"), dict) else {}
    container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
    if not container_tree:
        return

    def modifier_true(value: Any) -> bool:
        if value is True or value == 1:
            return True
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes"}
        return False

    def node_invisible(node: dict[str, Any]) -> bool:
        if modifier_true(node.get("invisible")):
            return True
        attributes = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
        modifiers = node.get("modifiers") if isinstance(node.get("modifiers"), dict) else {}
        attribute_modifiers = attributes.get("modifiers") if isinstance(attributes.get("modifiers"), dict) else {}
        return any(
            modifier_true(value)
            for value in (
                attributes.get("invisible"),
                modifiers.get("invisible"),
                attribute_modifiers.get("invisible"),
            )
        )

    visible_widget_ids: set[str] = set()

    def walk(rows: list[Any]) -> None:
        for row in rows:
            if not isinstance(row, dict):
                continue
            node_type = str(row.get("type") or row.get("containerType") or "").strip().lower()
            if node_type == "field" and not node_invisible(row):
                widget_id = str(row.get("widgetId") or "").strip()
                if not widget_id:
                    field_name = str(row.get("name") or row.get("field") or "").strip()
                    widget_id = f"field.{field_name}" if field_name else ""
                if widget_id:
                    visible_widget_ids.add(widget_id)
            for key in ("children", "pages", "tabs", "nodes", "items"):
                children = row.get(key)
                if isinstance(children, list):
                    walk(children)

    walk(container_tree)
    if not visible_widget_ids:
        return
    status_contract = contract_v2.get("statusContract") if isinstance(contract_v2.get("statusContract"), dict) else {}
    widget_status = status_contract.get("widgetStatus") if isinstance(status_contract.get("widgetStatus"), list) else []
    seen: set[str] = set()
    for row in widget_status:
        if not isinstance(row, dict):
            continue
        widget_id = str(row.get("widgetId") or "").strip()
        if widget_id not in visible_widget_ids:
            continue
        seen.add(widget_id)
        row["visible"] = True
        if row.get("readonly") is True:
            row["auth"] = "read"
        elif row.get("disabled") is not True:
            row["auth"] = "edit"
    for widget_id in sorted(visible_widget_ids - seen):
        widget_status.append({
            "widgetId": widget_id,
            "visible": True,
            "readonly": False,
            "required": False,
            "disabled": False,
            "auth": "edit",
        })
    set_v2_widget_status(contract_v2, widget_status)


def form_layout_governance(source_contract: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(source_contract, dict):
        return {}
    profile = source_contract.get("business_operation_profile")
    if not isinstance(profile, dict):
        return {}
    governance = profile.get("form_structure_governance")
    return governance if isinstance(governance, dict) else {}


def form_layout_governance_columns(source_contract: dict[str, Any] | None, title: str = "") -> int:
    governance = form_layout_governance(source_contract)
    return form_layout_columns_from_governance(governance, title)


def form_layout_columns_from_governance(governance: dict[str, Any] | None, title: str = "") -> int:
    if not isinstance(governance, dict):
        return 0
    group_columns = governance.get("group_columns") if isinstance(governance.get("group_columns"), dict) else {}
    columns = 0
    key = str(title or "").strip()
    if key:
        try:
            columns = int(group_columns.get(key) or 0)
        except (TypeError, ValueError):
            columns = 0
    if columns <= 0:
        try:
            columns = int(governance.get("form_columns") or 0)
        except (TypeError, ValueError):
            columns = 0
    return columns if columns > 0 else 0


def form_layout_group_visible_from_governance(governance: dict[str, Any] | None, title: str = "") -> bool:
    if not isinstance(governance, dict):
        return True
    group_visibility = governance.get("group_visibility") if isinstance(governance.get("group_visibility"), dict) else {}
    key = str(title or "").strip()
    if not key or key not in group_visibility:
        return True
    return bool(group_visibility.get(key))


def apply_form_layout_governance_to_group(
    node: dict[str, Any],
    title: str = "",
    *,
    source_contract: dict[str, Any] | None = None,
) -> None:
    if not isinstance(node, dict):
        return
    resolved_title = str(
        title
        or node.get("string")
        or node.get("label")
        or node.get("title")
        or node.get("name")
        or ""
    ).strip()
    columns = form_layout_governance_columns(source_contract, resolved_title)
    if columns <= 0:
        return
    node["cols"] = columns
    node["columns"] = columns
    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
    attrs["col"] = str(columns)
    node["attributes"] = attrs


def apply_business_config_form_groups(
    contract: dict[str, Any],
    governance: dict[str, Any],
    *,
    source_contract: dict[str, Any] | None = None,
) -> None:
    layout_contract = contract.get("layoutContract") if isinstance(contract.get("layoutContract"), dict) else {}
    container_tree = layout_contract.get("containerTree") if isinstance(layout_contract.get("containerTree"), list) else []
    if not container_tree:
        return
    hidden_field_names = {
        str(item or "").strip()
        for item in (governance.get("hidden_field_names") or [])
        if str(item or "").strip()
    }

    def node_field_name(node: Any) -> str:
        if not isinstance(node, dict):
            return ""
        return str(node.get("name") or node.get("field") or node.get("fieldCode") or "").strip()

    def remove_fields(
        nodes: list[Any],
        names: set[str],
        *,
        collect: dict[str, dict[str, Any]] | None = None,
        include_widget_nodes: bool = True,
    ) -> list[Any]:
        out: list[Any] = []
        for node in nodes:
            if not isinstance(node, dict):
                out.append(node)
                continue
            node_type = str(node.get("type") or node.get("containerType") or "").strip().lower()
            name = node_field_name(node)
            is_field_node = node_type == "field" or (
                include_widget_nodes and bool(str(node.get("widgetId") or "").strip())
            )
            if is_field_node and name in names:
                if collect is not None:
                    collect.setdefault(name, deepcopy(node))
                continue
            next_node = node
            for key in ("children", "pages", "tabs", "nodes", "items", "widgetList"):
                children = next_node.get(key)
                if isinstance(children, list):
                    next_node = dict(next_node)
                    next_node[key] = remove_fields(
                        children,
                        names,
                        collect=collect,
                        include_widget_nodes=include_widget_nodes,
                    )
            out.append(next_node)
        return out

    if hidden_field_names:
        container_tree = remove_fields(container_tree, hidden_field_names)
        structure = contract.get("formStructureContract") if isinstance(contract.get("formStructureContract"), dict) else {}
        roles = structure.get("fieldRoles") if isinstance(structure.get("fieldRoles"), dict) else {}
        if roles:
            structure["fieldRoles"] = {name: role for name, role in roles.items() if name not in hidden_field_names}
        set_v2_container_tree(contract, container_tree)

    field_groups = governance.get("field_groups") if isinstance(governance.get("field_groups"), dict) else {}
    configured_groups: list[tuple[str, list[str]]] = []
    configured_names: set[str] = set()
    for raw_title, raw_names in field_groups.items():
        title = str(raw_title or "").strip()
        if title and not form_layout_group_visible_from_governance(governance, title):
            continue
        names = [
            str(name or "").strip()
            for name in (raw_names if isinstance(raw_names, list) else [])
            if str(name or "").strip()
        ]
        names = [name for name in names if name not in hidden_field_names and name not in configured_names]
        if not title or not names:
            continue
        configured_names.update(names)
        configured_groups.append((title, names))
    if not configured_groups:
        return

    moved_nodes: dict[str, dict[str, Any]] = {}
    container_tree = remove_fields(
        container_tree,
        configured_names,
        collect=moved_nodes,
        include_widget_nodes=False,
    )

    def group_title(node: Any) -> str:
        if not isinstance(node, dict):
            return ""
        if str(node.get("type") or node.get("containerType") or "").strip().lower() != "group":
            return ""
        return str(node.get("string") or node.get("label") or node.get("title") or "").strip()

    def find_group(nodes: list[Any], title: str) -> dict[str, Any] | None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if group_title(node) == title:
                return node
            for key in ("children", "pages", "tabs", "nodes", "items"):
                children = node.get(key)
                if isinstance(children, list):
                    found = find_group(children, title)
                    if found is not None:
                        return found
        return None

    for index, (title, names) in enumerate(configured_groups, start=1):
        group = find_group(container_tree, title)
        if group is None:
            group = {
                "type": "group",
                "name": "business_config_group_%s" % index,
                "string": title,
                "label": title,
                "children": [],
                "widgetList": [],
            }
            container_tree.append(group)
        apply_form_layout_governance_to_group(group, title, source_contract=source_contract)
        children = group.get("children") if isinstance(group.get("children"), list) else []
        children.extend(deepcopy(moved_nodes[name]) for name in names if name in moved_nodes)
        group["children"] = children

    set_v2_container_tree(contract, container_tree)
