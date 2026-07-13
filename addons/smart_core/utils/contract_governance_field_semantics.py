# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


_PROJECT_FORM_PAGE_PRESERVE_FIELDS: set[str] = set()
_BUSINESS_DETAIL_RELATION_FIELDS: set[str] = set()
_TECHNICAL_RELATION_FIELD_PREFIXES: tuple[str, ...] = ()
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


def is_technical_field(name: str, descriptor: dict) -> bool:
    low = _safe_lower(name)
    if not low:
        return True
    if low in _PROJECT_FORM_PAGE_PRESERVE_FIELDS:
        return False
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    if (
        ttype in {"one2many", "many2many"}
        and low in _BUSINESS_DETAIL_RELATION_FIELDS
        and not low.startswith(_TECHNICAL_RELATION_FIELD_PREFIXES)
    ):
        return False
    if low in {"id", "__last_update", "display_name"}:
        return True
    if low.startswith(("create_", "write_", "message_", "activity_", "access_", "alias_", "website_")):
        return True
    if low.endswith(("_ids", "_id_count")) and low not in {
        "project_type_id",
        "project_category_id",
        "stage_id",
        "manager_id",
        "user_id",
        "owner_id",
        "company_id",
    }:
        return True
    if ttype in {"one2many", "many2many", "properties_definition"}:
        return True
    return False


def classify_field_semantic_type(name: str, descriptor: dict) -> str:
    low = _safe_lower(name)
    ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
    if is_technical_field(name, descriptor):
        return "technical"
    if ttype in {"many2one", "one2many", "many2many"}:
        return "relation"
    if descriptor.get("compute") or descriptor.get("related"):
        return "computed"
    if low in {"active", "company_id", "create_uid", "create_date", "write_uid", "write_date"}:
        return "system"
    return "business"


def _collect_layout_field_names(nodes: Any) -> list[str]:
    ordered: list[str] = []

    def _iter_children(node: dict) -> list[list]:
        rows: list[list] = []
        for key in ("children", "tabs", "pages", "nodes", "items"):
            candidate = node.get(key)
            if isinstance(candidate, list):
                rows.append(candidate)
        return rows

    def _collect(items: list) -> None:
        for node in items:
            if not isinstance(node, dict):
                continue
            if _safe_lower(node.get("type")) == "field":
                name = _safe_text(node.get("name"))
                if name and name not in ordered:
                    ordered.append(name)
            for children in _iter_children(node):
                _collect(children)

    if isinstance(nodes, list):
        _collect(nodes)
    elif isinstance(nodes, dict):
        _collect([nodes])
    return ordered


def annotate_field_semantics(data: dict) -> None:
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout_field_set = set(_collect_layout_field_names(form.get("layout")))
    field_groups = data.get("field_groups") if isinstance(data.get("field_groups"), list) else []
    core_set: set[str] = set()
    advanced_set: set[str] = set()
    for item in field_groups:
        if not isinstance(item, dict):
            continue
        key = _safe_lower(item.get("name"))
        names = item.get("fields") if isinstance(item.get("fields"), list) else []
        normalized = {_safe_text(name) for name in names if _safe_text(name)}
        if key == "core":
            core_set.update(normalized)
        elif key == "advanced":
            advanced_set.update(normalized)

    field_policies = _as_dict(data.get("field_policies"))
    semantics_map: dict[str, dict[str, Any]] = {}
    for field_name, raw_descriptor in list(fields_map.items()):
        descriptor = _as_dict(raw_descriptor)
        if not descriptor:
            continue
        semantic_type = classify_field_semantic_type(field_name, descriptor)
        ttype = _safe_lower(descriptor.get("type") or descriptor.get("ttype"))
        is_layout_relation = (
            field_name in layout_field_set
            and ttype in {"many2one", "one2many", "many2many"}
            and not _safe_lower(field_name).startswith(("message_", "activity_", "rating_", "website_"))
        )
        if semantic_type == "technical" and is_layout_relation:
            semantic_type = "relation"
        policy = _as_dict(field_policies.get(field_name))
        policy_group = _safe_lower(policy.get("group"))
        visible_profiles = policy.get("visible_profiles") if isinstance(policy.get("visible_profiles"), list) else []
        normalized_profiles = {_safe_lower(item) for item in visible_profiles if _safe_text(item)}
        has_surface_visibility = bool(
            normalized_profiles
            & {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY}
        )

        if policy_group in {"core", "advanced"}:
            surface_role = policy_group
        elif field_name in core_set:
            surface_role = "core"
        elif field_name in advanced_set:
            surface_role = "advanced"
        elif semantic_type == "technical" or not has_surface_visibility:
            surface_role = "hidden"
        else:
            surface_role = "advanced"

        descriptor["semantic_type"] = semantic_type
        descriptor["surface_role"] = surface_role
        descriptor["technical"] = semantic_type == "technical"
        fields_map[field_name] = descriptor
        semantics_map[field_name] = {
            "semantic_type": semantic_type,
            "surface_role": surface_role,
            "technical": semantic_type == "technical",
        }

    data["fields"] = fields_map
    data["field_semantics"] = semantics_map
