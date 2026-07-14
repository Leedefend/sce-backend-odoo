# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def _clear_create_actions(data: dict) -> None:
    toolbar = _as_dict(data.get("toolbar"))
    if isinstance(toolbar.get("header"), list):
        toolbar["header"] = []
    data["toolbar"] = toolbar
    data["buttons"] = []
    data["action_groups"] = []


def govern_enterprise_company_form(
    data: dict,
    *,
    form_fields: tuple[str, ...],
    field_labels: dict[str, str],
    make_labeled_field_node: Any,
    resolve_render_profile: Any,
    render_profile_create: str,
    inject_enterprise_form_governance: Any,
) -> None:
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in form_fields if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "企业基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_company_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_company_core_group",
                    "string": "企业基础信息",
                    "children": [
                        make_labeled_field_node(name, fields_map, field_labels)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if resolve_render_profile(data) == render_profile_create:
        _clear_create_actions(data)
    inject_enterprise_form_governance(
        data,
        next_action_key="department",
        next_action_label="进入组织架构",
    )


def govern_enterprise_department_form(
    data: dict,
    *,
    form_fields: tuple[str, ...],
    field_labels: dict[str, str],
    make_labeled_field_node: Any,
    resolve_render_profile: Any,
    render_profile_create: str,
    inject_enterprise_form_governance: Any,
) -> None:
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in form_fields if name in fields_map]
    if not selected:
        return
    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "core",
            "label": "组织基础信息",
            "priority": 1,
            "collapsible": False,
            "fields": selected,
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_department_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_department_core_group",
                    "string": "组织基础信息",
                    "children": [
                        make_labeled_field_node(name, fields_map, field_labels)
                        for name in selected
                    ],
                }
            ],
        }
    ]
    views["form"] = form
    data["views"] = views

    if resolve_render_profile(data) == render_profile_create:
        _clear_create_actions(data)
    inject_enterprise_form_governance(
        data,
        next_action_key="user",
        next_action_label="进入用户设置",
    )


def govern_enterprise_user_form(
    data: dict,
    *,
    form_fields: tuple[str, ...],
    make_labeled_field_node: Any,
    resolve_contract_required_fields: Any,
    to_bool: Any,
    render_profile_create: str,
    render_profile_edit: str,
    render_profile_readonly: str,
    inject_enterprise_form_governance: Any,
) -> None:
    fields_map = _as_dict(data.get("fields"))
    selected = [name for name in form_fields if name in fields_map]
    if not selected:
        return
    account_fields = {"login", "name", "active", "password"}
    contact_fields = {"phone", "email"}
    assignment_fields = {
        "company_id",
        "sc_department_id",
        "sc_manager_user_id",
        "sc_role_profile",
        "sc_role_effective",
        "sc_role_landing_label",
    }
    permission_fields = {"sc_user_role_group_ids"}

    data["visible_fields"] = selected
    data["field_groups"] = [
        {
            "name": "account",
            "label": "账号信息",
            "priority": 1,
            "collapsible": False,
            "fields": [name for name in selected if name in account_fields],
        },
        {
            "name": "contact",
            "label": "联系方式",
            "priority": 2,
            "collapsible": False,
            "fields": [name for name in selected if name in contact_fields],
        },
        {
            "name": "assignment",
            "label": "组织归属",
            "priority": 3,
            "collapsible": False,
            "fields": [name for name in selected if name in assignment_fields],
        },
        {
            "name": "permissions",
            "label": "业务角色",
            "priority": 4,
            "collapsible": False,
            "fields": [name for name in selected if name in permission_fields],
        },
    ]
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    form["layout"] = [
        {
            "type": "sheet",
            "name": "enterprise_user_form_sheet",
            "children": [
                {
                    "type": "group",
                    "name": "enterprise_user_basic_group",
                    "string": "账号信息",
                    "children": [
                        make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in account_fields
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_contact_group",
                    "string": "联系方式",
                    "children": [
                        make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in contact_fields
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_assignment_group",
                    "string": "组织归属",
                    "children": [
                        make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in assignment_fields
                    ],
                },
                {
                    "type": "group",
                    "name": "enterprise_user_permissions_group",
                    "string": "业务角色",
                    "children": [
                        make_labeled_field_node(name, fields_map)
                        for name in selected
                        if name in permission_fields
                    ],
                },
            ],
        }
    ]
    form["statusbar"] = {"field": None, "states": []}
    form["header_buttons"] = []
    form["button_box"] = []
    form["stat_buttons"] = []
    views["form"] = form
    data["views"] = views

    field_policies = _as_dict(data.get("field_policies"))
    basic_fields = {"name", "login", "password", "phone", "email", "active", "sc_user_role_group_ids"}
    readonly_fields = {"sc_role_effective", "sc_role_landing_label"}
    contract_required_fields = set(resolve_contract_required_fields(data, fields_map))
    for name in selected:
        descriptor = _as_dict(fields_map.get(name))
        readonly = name in readonly_fields or to_bool(descriptor.get("readonly"), fallback=False)
        field_policies[name] = {
            "visible_profiles": [
                render_profile_create,
                render_profile_edit,
                render_profile_readonly,
            ],
            "required_profiles": (
                [render_profile_create, render_profile_edit]
                if name in contract_required_fields and not readonly
                else []
            ),
            "readonly_profiles": (
                [render_profile_create, render_profile_edit, render_profile_readonly]
                if readonly
                else [render_profile_readonly]
            ),
            "source_required": name in contract_required_fields and not readonly,
            "source_readonly": readonly,
            "group": "core" if name in basic_fields else "secondary",
        }
    data["field_policies"] = field_policies

    _clear_create_actions(data)
    inject_enterprise_form_governance(data)
