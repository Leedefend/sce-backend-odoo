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
