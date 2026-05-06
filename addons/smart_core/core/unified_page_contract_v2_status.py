# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .source_authority import build_source_authority_contract

AUTH_LEVELS = {"none", "read", "edit", "admin"}
SOURCE_KIND = "unified_page_contract_v2_status_projection"
SOURCE_AUTHORITIES = ("permission_surface", "access_policy", "field_modifiers", "button_status")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> dict[str, Any]:
    return build_source_authority_contract(
        kind=SOURCE_KIND,
        authorities=SOURCE_AUTHORITIES,
        no_business_fact_authority=NO_BUSINESS_FACT_AUTHORITY,
        runtime_carrier="unified_page_contract_v2_status",
    )

DENY_STATES = {"deny", "denied", "blocked", "forbidden", "unauthorized"}
READONLY_STATES = {"readonly", "read_only", "read"}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _bool_or_none(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _stable_id(value: Any, fallback: str) -> str:
    raw = _text(value, fallback)
    out = []
    for char in raw:
        if char.isalnum() or char in "_.:-":
            out.append(char)
        elif char in " /":
            out.append(".")
    normalized = "".join(out).strip(".")
    if not normalized:
        normalized = fallback
    if not normalized[0].isalpha():
        normalized = f"id.{normalized}"
    return normalized


def _widget_id(field_name: str) -> str:
    return f"field.{_stable_id(field_name, 'field')}"


def _button_id(action_key: str) -> str:
    raw = _stable_id(action_key, "action")
    return raw if raw.startswith("btn.") else f"btn.{raw}"


def _auth_from_rights(rights: dict[str, Any], fallback: str = "read") -> str:
    if rights.get("admin") is True:
        return "admin"
    if rights.get("write") is True or rights.get("create") is True:
        return "edit"
    if rights.get("read") is True:
        return "read"
    if rights and not any(bool(v) for v in rights.values()):
        return "none"
    return fallback if fallback in AUTH_LEVELS else "read"


def _resolve_global_status(source: dict[str, Any]) -> dict[str, Any]:
    permission = _dict(source.get("permission_surface"))
    access = _dict(source.get("access_policy"))
    permissions = _dict(source.get("permissions"))
    effective = _dict(permission.get("effective"))
    rights = _dict(effective.get("rights")) or _dict(permission.get("rights")) or _dict(permissions.get("effective"))
    allowed = permission.get("allowed")
    if allowed is None:
        allowed = access.get("allowed")
    if allowed is None:
        allowed = True
    reason = _text(permission.get("reason_code") or access.get("reason_code") or permissions.get("reason_code"))
    auth = _auth_from_rights(rights, fallback="read" if allowed else "none")
    if allowed is False:
        auth = "none"
    return {
        "pageVisible": bool(allowed),
        "pageAuth": auth,
        **({"reasonCode": reason} if reason else {}),
    }


def _merge_bool(target: dict[str, Any], key: str, value: Any) -> None:
    flag = _bool_or_none(value)
    if flag is not None:
        target[key] = flag


def _field_policy_row(field_name: str, policy: dict[str, Any], *, render_profile: str) -> dict[str, Any]:
    row = {
        "widgetId": _widget_id(field_name),
        "visible": True,
        "readonly": False,
        "required": False,
        "disabled": False,
        "auth": "edit",
    }
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
        _merge_bool(row, key, policy.get(key))
    reason = _text(policy.get("reason_code") or policy.get("reasonCode"))
    if reason:
        row["reasonCode"] = reason
    if row.get("readonly") is True:
        row["auth"] = "read"
    if row.get("visible") is False or row.get("disabled") is True:
        row["auth"] = "none" if row.get("visible") is False else row["auth"]
    return row


def _apply_field_meta(row: dict[str, Any], meta: dict[str, Any]) -> None:
    for key in ("readonly", "required"):
        _merge_bool(row, key, meta.get(key))
    if row.get("readonly") is True:
        row["auth"] = "read"
    elif row.get("disabled") is not True and row.get("visible") is not False:
        row["auth"] = "edit"


def _apply_modifiers(row: dict[str, Any], modifiers: dict[str, Any]) -> None:
    if "invisible" in modifiers:
        invisible = _bool_or_none(modifiers.get("invisible"))
        if invisible is not None:
            row["visible"] = not invisible
    for key in ("readonly", "required"):
        _merge_bool(row, key, modifiers.get(key))
    reason = _text(modifiers.get("reason_code") or modifiers.get("reasonCode"))
    if reason:
        row["reasonCode"] = reason
    if row.get("readonly") is True:
        row["auth"] = "read"
    if row.get("visible") is False:
        row["auth"] = "none"


def _validation_required_fields(source: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    validation = _dict(source.get("validation_surface"))
    for field_name in _list(validation.get("required_fields")):
        if _text(field_name):
            out.add(_text(field_name))
    for rule in _list(validation.get("field_rules")) + _list(source.get("validation_rules")):
        if not isinstance(rule, dict):
            continue
        if _text(rule.get("rule") or rule.get("code")).lower() == "required" and _text(rule.get("field")):
            out.add(_text(rule.get("field")))
    return out


def _field_meta_index(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    meta_fields = source.get("meta_fields")
    if isinstance(meta_fields, list):
        for row in meta_fields:
            if isinstance(row, dict) and _text(row.get("name")):
                out[_text(row.get("name"))] = row
    fields = source.get("fields")
    if isinstance(fields, dict):
        for key, row in fields.items():
            if isinstance(row, dict):
                copied = dict(row)
                copied.setdefault("name", key)
                out.setdefault(_text(key), copied)
    return out


def build_status_contract_v2(source_contract: dict[str, Any], *, render_profile: str = "edit") -> dict[str, Any]:
    source = _dict(source_contract)
    status = {
        "globalStatus": _resolve_global_status(source),
        "containerStatus": [],
        "widgetStatus": [],
        "buttonStatus": [],
        "selectorStatus": [],
    }
    widget_index: dict[str, dict[str, Any]] = {}
    field_policies = _dict(source.get("field_policies"))
    for field_name, policy in field_policies.items():
        if not isinstance(policy, dict):
            continue
        row = _field_policy_row(_text(field_name), policy, render_profile=render_profile)
        widget_index[row["widgetId"]] = row
    for field_name, meta in _field_meta_index(source).items():
        widget_id = _widget_id(field_name)
        row = widget_index.setdefault(
            widget_id,
            {
                "widgetId": widget_id,
                "visible": True,
                "readonly": False,
                "required": False,
                "disabled": False,
                "auth": "edit",
            },
        )
        _apply_field_meta(row, meta)
    for field_name in _validation_required_fields(source):
        widget_id = _widget_id(field_name)
        row = widget_index.setdefault(
            widget_id,
            {
                "widgetId": widget_id,
                "visible": True,
                "readonly": False,
                "required": False,
                "disabled": False,
                "auth": "edit",
            },
        )
        row["required"] = True
    for field_name, modifiers in _dict(source.get("modifiers") or source.get("modifiers_patch")).items():
        if not isinstance(modifiers, dict):
            continue
        widget_id = _widget_id(_text(field_name))
        row = widget_index.setdefault(
            widget_id,
            {
                "widgetId": widget_id,
                "visible": True,
                "readonly": False,
                "required": False,
                "disabled": False,
                "auth": "edit",
            },
        )
        _apply_modifiers(row, modifiers)
    status["widgetStatus"] = [deepcopy(widget_index[key]) for key in sorted(widget_index)]
    status["buttonStatus"] = _build_button_status(source)
    status["containerStatus"] = _build_container_status(source)
    status["selectorStatus"] = _build_selector_status(source)
    return status


def _build_button_status(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for action_key, policy in _dict(source.get("action_policies")).items():
        if not isinstance(policy, dict):
            continue
        state = _text(policy.get("state") or policy.get("capability_state")).lower()
        enabled = policy.get("enabled")
        visible = policy.get("visible")
        row = {
            "btnId": _button_id(_text(action_key)),
            "visible": True if visible is None else bool(visible),
            "disabled": False,
        }
        if enabled is False or state in DENY_STATES or state in READONLY_STATES:
            row["disabled"] = True
        reason = _text(policy.get("reason_code") or policy.get("reasonCode"))
        if reason:
            row["reasonCode"] = reason
        out.append(row)
    return sorted(out, key=lambda row: row["btnId"])


def _build_container_status(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for container_id, policy in _dict(source.get("container_policies")).items():
        if not isinstance(policy, dict):
            continue
        row = {"containerId": _stable_id(container_id, "container"), "visible": True, "disabled": False}
        _merge_bool(row, "visible", policy.get("visible"))
        _merge_bool(row, "disabled", policy.get("disabled"))
        reason = _text(policy.get("reason_code") or policy.get("reasonCode"))
        if reason:
            row["reasonCode"] = reason
        out.append(row)
    return sorted(out, key=lambda row: row["containerId"])


def _build_selector_status(source: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in _list(source.get("selector_status") or source.get("selectorStatus")):
        if not isinstance(row, dict) or not _text(row.get("selector")):
            continue
        normalized = {"selector": _text(row.get("selector"))}
        for key in ("visible", "readonly", "required", "disabled"):
            _merge_bool(normalized, key, row.get(key))
        reason = _text(row.get("reason_code") or row.get("reasonCode"))
        if reason:
            normalized["reasonCode"] = reason
        out.append(normalized)
    return sorted(out, key=lambda row: row["selector"])
