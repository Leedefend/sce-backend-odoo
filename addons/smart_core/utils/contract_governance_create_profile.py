# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


_RENDER_PROFILE_CREATE = "create"


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def is_create_render_profile(data: dict) -> bool:
    raw = _safe_lower(data.get("render_profile"))
    if raw == _RENDER_PROFILE_CREATE:
        return True
    head = _as_dict(data.get("head"))
    raw = _safe_lower(head.get("render_profile"))
    if raw == _RENDER_PROFILE_CREATE:
        return True
    record_id = data.get("record_id") or data.get("res_id") or head.get("record_id") or head.get("res_id")
    if record_id in (None, "", False, 0, "0", "new", "none", "false"):
        return True
    return False


def mark_record_dependent_native_buttons_hidden_on_create(
    data: dict,
    *,
    is_form_contract: Callable[[dict], bool],
) -> None:
    if not is_form_contract(data) or not is_create_render_profile(data):
        return
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    def _button_requires_record(node: dict) -> bool:
        action = _as_dict(node.get("action"))
        level = _safe_lower(action.get("level") or node.get("level"))
        kind = _safe_lower(action.get("kind") or node.get("kind"))
        button_type = _safe_lower(node.get("buttonType") or node.get("type"))
        if level in {"smart", "row", "record"}:
            return True
        if button_type == "object" or kind in {"server", "object"}:
            return True
        return False

    def _hide(node: dict) -> None:
        node["invisible"] = {"kind": "static", "value": True, "reason_code": "CREATE_PROFILE_REQUIRES_RECORD"}
        modifiers = _as_dict(node.get("modifiers"))
        modifiers["invisible"] = node["invisible"]
        node["modifiers"] = modifiers
        action = _as_dict(node.get("action"))
        if action:
            profiles = action.get("visible_profiles") if isinstance(action.get("visible_profiles"), list) else []
            action["visible_profiles"] = [p for p in profiles if _safe_lower(p) != _RENDER_PROFILE_CREATE]
            action["requires_record"] = True
            action["hidden_reason_code"] = "CREATE_PROFILE_REQUIRES_RECORD"
            node["action"] = action

    def _walk(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                _walk(item)
            return
        if not isinstance(obj, dict):
            return
        node_type = _safe_lower(obj.get("type") or obj.get("kind"))
        if node_type == "button" and _button_requires_record(obj):
            _hide(obj)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            _walk(obj.get(key))

    _walk(layout)
    form["layout"] = layout
    views["form"] = form
    data["views"] = views


def is_create_profile_noise_field(name: str, descriptor: dict) -> bool:
    low = _safe_lower(name)
    if not low:
        return True
    if low in {
        "active",
        "partner_gid",
        "additional_info",
        "same_vat_partner_id",
        "same_company_registry_partner_id",
        "commercial_partner_id",
        "property_account_receivable_id",
        "property_account_payable_id",
        "phone_blacklisted",
        "mobile_blacklisted",
        "is_blacklisted",
        "active_lang_count",
        "duplicated_bank_account_partners_count",
        "show_credit_limit",
        "hide_peppol_fields",
        "fiscal_country_codes",
        "country_code",
    }:
        return True
    if low.endswith("_count") or low.endswith("_counter"):
        return True
    if low.startswith(("same_", "duplicated_", "hide_", "show_", "blacklist", "peppol_")):
        return True
    if bool(descriptor.get("readonly")) and (descriptor.get("compute") or descriptor.get("related")):
        return True
    return False


def hide_create_profile_noise_fields(
    data: dict,
    *,
    is_form_contract: Callable[[dict], bool],
    is_enterprise_user_form_contract: Callable[[dict], bool],
) -> None:
    if not is_form_contract(data) or not is_create_render_profile(data):
        return
    fields_map = _as_dict(data.get("fields"))
    if not fields_map:
        return
    hidden_names: set[str] = set()
    semantics_map = _as_dict(data.get("field_semantics"))
    for name, raw_descriptor in list(fields_map.items()):
        descriptor = _as_dict(raw_descriptor)
        if is_enterprise_user_form_contract(data) and _safe_lower(name) == "active":
            continue
        if not descriptor or not is_create_profile_noise_field(name, descriptor):
            continue
        descriptor["semantic_type"] = "technical"
        descriptor["surface_role"] = "hidden"
        descriptor["technical"] = True
        fields_map[name] = descriptor
        semantics_map[name] = {
            "semantic_type": "technical",
            "surface_role": "hidden",
            "technical": True,
        }
        hidden_names.add(_safe_text(name))
    if not hidden_names:
        return
    data["fields"] = fields_map
    data["field_semantics"] = semantics_map

    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    hidden_modifier = {"kind": "static", "value": True, "reason_code": "CREATE_PROFILE_TECHNICAL_FIELD"}

    def _walk(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                _walk(item)
            return
        if not isinstance(obj, dict):
            return
        node_type = _safe_lower(obj.get("type") or obj.get("kind"))
        node_name = _safe_text(obj.get("name"))
        if node_type == "field" and node_name in hidden_names:
            obj["invisible"] = hidden_modifier
            modifiers = _as_dict(obj.get("modifiers"))
            modifiers["invisible"] = hidden_modifier
            obj["modifiers"] = modifiers
        for key in ("children", "tabs", "pages", "nodes", "items"):
            _walk(obj.get(key))

    _walk(layout)
    form["layout"] = layout
    views["form"] = form
    data["views"] = views


def hide_create_profile_state_ribbons(
    data: dict,
    *,
    is_form_contract: Callable[[dict], bool],
) -> None:
    if not is_form_contract(data) or not is_create_render_profile(data):
        return
    views = _as_dict(data.get("views"))
    form = _as_dict(views.get("form"))
    layout = form.get("layout")
    if not isinstance(layout, list):
        return

    hidden_modifier = {"kind": "static", "value": True, "reason_code": "CREATE_PROFILE_STATE_WIDGET"}

    def _is_archive_ribbon(node: dict) -> bool:
        if _safe_lower(node.get("type") or node.get("kind")) != "widget":
            return False
        widget = _safe_lower(node.get("widget") or node.get("name"))
        if widget != "web_ribbon":
            return False
        attrs = _as_dict(node.get("attributes"))
        merged = " ".join(
            _safe_text(value)
            for value in (
                node.get("title"),
                node.get("string"),
                node.get("label"),
                node.get("class"),
                attrs.get("title"),
                attrs.get("class"),
                attrs.get("bg_color"),
            )
            if value is not None
        ).lower()
        return any(token in merged for token in ("archive", "archived", "归档"))

    def _walk(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                _walk(item)
            return
        if not isinstance(obj, dict):
            return
        if _is_archive_ribbon(obj):
            obj["invisible"] = hidden_modifier
            modifiers = _as_dict(obj.get("modifiers"))
            modifiers["invisible"] = hidden_modifier
            obj["modifiers"] = modifiers
        for key in ("children", "tabs", "pages", "nodes", "items"):
            _walk(obj.get(key))

    _walk(layout)
    form["layout"] = layout
    views["form"] = form
    data["views"] = views
