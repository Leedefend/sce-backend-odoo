# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


_BUSINESS_DETAIL_RELATION_FIELDS: set[str] = set()
_FORM_CORE_FIELD_MAX = 6
_RENDER_PROFILE_CREATE = "create"
_RENDER_PROFILE_EDIT = "edit"
_RENDER_PROFILE_READONLY = "readonly"


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def iter_field_order(data: dict) -> list[str]:
    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect_fields(nodes: list, out: list[str]) -> None:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if _safe_lower(node.get("type")) == "field":
                name = _safe_text(node.get("name"))
                if name and name not in out:
                    out.append(name)
            for children in _iter_children(node):
                _collect_fields(children, out)

    ordered: list[str] = []
    form = _as_dict(_as_dict(data.get("views")).get("form"))
    layout = form.get("layout")
    _collect_fields(layout if isinstance(layout, list) else [], ordered)
    for name in (_as_dict(data.get("fields")) or {}).keys():
        if name not in ordered:
            ordered.append(name)
    return ordered


def derive_form_core_fields(
    data: dict,
    *,
    is_project_form: bool,
    project_form_profile: dict,
    is_technical_field: Callable[[str, dict], bool],
    to_bool: Callable[[Any], bool],
) -> list[str]:
    fields_map = _as_dict(data.get("fields"))
    ordered = iter_field_order(data)
    core: list[str] = []
    project_form_primary_fields = project_form_profile.get("primary_fields") or []
    project_form_create_hidden_fields = set(project_form_profile.get("create_hidden_fields") or [])

    def _push(name: str) -> None:
        if not name or name in core:
            return
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            return
        if is_technical_field(name, descriptor):
            return
        if is_project_form and name in project_form_create_hidden_fields:
            return
        core.append(name)

    if is_project_form:
        for name in project_form_primary_fields:
            _push(name)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break

    for name in ordered:
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            continue
        required = to_bool(descriptor.get("required"))
        readonly = to_bool(descriptor.get("readonly"))
        if is_project_form and name in project_form_create_hidden_fields:
            continue
        if required and not readonly:
            _push(name)
        if len(core) >= _FORM_CORE_FIELD_MAX:
            break

    if len(core) < _FORM_CORE_FIELD_MAX:
        for preferred in ("name", "display_name"):
            _push(preferred)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break

    if len(core) < _FORM_CORE_FIELD_MAX:
        for name in ordered:
            _push(name)
            if len(core) >= _FORM_CORE_FIELD_MAX:
                break
    for name in ordered:
        descriptor = _as_dict(fields_map.get(name))
        if not descriptor:
            continue
        ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
        if ttype in {"one2many", "many2many"} and name in _BUSINESS_DETAIL_RELATION_FIELDS and name not in core:
            if len(core) >= _FORM_CORE_FIELD_MAX:
                core[-1] = name
            else:
                core.append(name)
            break
    return core[:_FORM_CORE_FIELD_MAX]


def apply_form_field_groups(
    data: dict,
    *,
    is_form_contract: Callable[[dict], bool],
    is_project_form: bool,
    project_form_profile: dict,
    is_enterprise_company_form: bool,
    is_enterprise_user_form: bool,
    is_technical_field: Callable[[str, dict], bool],
    to_bool: Callable[[Any], bool],
) -> None:
    if not is_form_contract(data):
        return
    existing_groups = data.get("field_groups") if isinstance(data.get("field_groups"), list) else []
    if existing_groups and (is_enterprise_company_form or is_enterprise_user_form):
        return
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    core_fields = derive_form_core_fields(
        data,
        is_project_form=is_project_form,
        project_form_profile=project_form_profile,
        is_technical_field=is_technical_field,
        to_bool=to_bool,
    )
    core_set = set(core_fields)
    advanced_fields = [
        name
        for name in iter_field_order(data)
        if name in fields_map and name not in core_set
    ]
    data["field_groups"] = [
        {
            "name": "core",
            "label": "核心信息",
            "priority": 1,
            "collapsible": False,
            "fields": core_fields,
        },
        {
            "name": "advanced",
            "label": "高级信息",
            "priority": 2,
            "collapsible": True,
            "collapsed_by_default": True,
            "fields": advanced_fields,
        },
    ]


def resolve_contract_required_fields(
    data: dict,
    fields_map: dict[str, Any],
    *,
    is_project_form: bool,
    to_bool: Callable[[Any], bool],
) -> list[str]:
    if is_project_form:
        descriptor = _as_dict(fields_map.get("name"))
        if descriptor and not to_bool(descriptor.get("readonly")):
            return ["name"]
        return []
    required_fields: list[str] = []
    for name, descriptor_raw in fields_map.items():
        descriptor = _as_dict(descriptor_raw)
        if not descriptor:
            continue
        semantic_type = _safe_lower(descriptor.get("semantic_type"))
        surface_role = _safe_lower(descriptor.get("surface_role"))
        if semantic_type == "technical" or surface_role == "hidden":
            continue
        required = to_bool(descriptor.get("required"))
        readonly = to_bool(descriptor.get("readonly"))
        if required and not readonly:
            required_fields.append(name)
    return required_fields


def build_form_field_policies(
    data: dict,
    *,
    contract_required_fields: list[str],
    is_project_form: bool,
    project_form_profile: dict,
    to_bool: Callable[[Any], bool],
) -> dict[str, dict[str, Any]]:
    fields_map = _as_dict(data.get("fields"))
    core_group = {}
    advanced_group = {}
    for item in data.get("field_groups") if isinstance(data.get("field_groups"), list) else []:
        if not isinstance(item, dict):
            continue
        key = _safe_lower(item.get("name"))
        rows = item.get("fields")
        if not isinstance(rows, list):
            continue
        normalized = [str(name).strip() for name in rows if str(name).strip()]
        if key == "core":
            core_group = {name: True for name in normalized}
        if key == "advanced":
            advanced_group = {name: True for name in normalized}

    policies: dict[str, dict[str, Any]] = {}
    required_set = set(contract_required_fields)
    project_form_create_hidden_fields = set(project_form_profile.get("create_hidden_fields") or [])
    for name, descriptor_raw in fields_map.items():
        descriptor = _as_dict(descriptor_raw)
        if not descriptor:
            continue
        required = name in required_set
        readonly = to_bool(descriptor.get("readonly"))
        visible_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        if name in advanced_group:
            visible_profiles = [_RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
            if is_project_form and name not in project_form_create_hidden_fields:
                visible_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        required_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT] if required and not readonly else []
        readonly_profiles = [_RENDER_PROFILE_READONLY]
        if readonly:
            readonly_profiles = [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
        policies[name] = {
            "visible_profiles": visible_profiles,
            "required_profiles": required_profiles,
            "readonly_profiles": readonly_profiles,
            "source_required": required,
            "source_readonly": readonly,
            "group": "core" if name in core_group else ("advanced" if name in advanced_group else "secondary"),
        }
        if is_project_form and name in project_form_create_hidden_fields:
            policies[name]["visible_profiles"] = [_RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
            policies[name]["required_profiles"] = []
            policies[name]["readonly_profiles"] = [
                _RENDER_PROFILE_CREATE,
                _RENDER_PROFILE_EDIT,
                _RENDER_PROFILE_READONLY,
            ]
            policies[name]["source_required"] = False
            policies[name]["source_readonly"] = True
            policies[name]["group"] = "advanced"
    return policies
