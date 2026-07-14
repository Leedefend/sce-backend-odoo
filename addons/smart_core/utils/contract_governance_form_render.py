# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


_RENDER_PROFILE_CREATE = "create"
_RENDER_PROFILE_EDIT = "edit"
_RENDER_PROFILE_READONLY = "readonly"
_RENDER_PROFILES = {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY}


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def to_bool(value: Any, fallback: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return fallback
    lowered = str(value).strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    return fallback


def resolve_render_profile(data: dict) -> str:
    explicit = _safe_text(data.get("render_profile")).lower()
    if explicit in _RENDER_PROFILES:
        return explicit
    head = _as_dict(data.get("head"))
    view_type = _safe_text(head.get("view_type") or data.get("view_type")).lower()
    if view_type and "form" not in view_type:
        return _RENDER_PROFILE_EDIT
    effective = _as_dict(_as_dict(data.get("permissions")).get("effective")).get("rights")
    effective_rights = _as_dict(effective)
    head_permissions = _as_dict(head.get("permissions"))
    can_write = to_bool(
        effective_rights.get("write", head_permissions.get("write")),
        fallback=False,
    )
    can_create = to_bool(
        effective_rights.get("create", head_permissions.get("create")),
        fallback=False,
    )
    if not can_write and not can_create:
        return _RENDER_PROFILE_READONLY
    has_record = False
    for raw in (data.get("res_id"), head.get("res_id"), data.get("id")):
        if raw in (None, "", False):
            continue
        token = str(raw).strip().lower()
        if token in {"", "0", "new", "false", "null", "none"}:
            continue
        try:
            if int(token) > 0:
                has_record = True
                break
        except Exception:
            continue
    return _RENDER_PROFILE_EDIT if has_record else _RENDER_PROFILE_CREATE


def apply_form_view_capabilities(data: dict) -> None:
    form = _as_dict(_as_dict(data.get("views")).get("form"))
    capabilities = _as_dict(form.get("capabilities"))
    if not capabilities:
        return
    permission_root = _as_dict(data.get("permissions"))
    effective = _as_dict(permission_root.get("effective"))
    effective_rights = _as_dict(effective.get("rights"))
    head = _as_dict(data.get("head"))
    head_permissions = _as_dict(head.get("permissions"))

    if capabilities.get("can_create") is False:
        effective_rights["create"] = False
        head_permissions["create"] = False
    if capabilities.get("can_write") is False:
        effective_rights["write"] = False
        head_permissions["write"] = False
    if capabilities.get("can_delete") is False:
        effective_rights["unlink"] = False
        head_permissions["unlink"] = False

    effective["rights"] = effective_rights
    permission_root["effective"] = effective
    data["permissions"] = permission_root
    head["permissions"] = head_permissions
    data["head"] = head
