# -*- coding: utf-8 -*-
"""Helpers for resolving load_contract entry context from menu/action hints."""

from __future__ import annotations

import re
from typing import Any, Iterable, List

from odoo import SUPERUSER_ID, api


def resolve_entry_action(env, *, su_env=None, menu_id=None, action_id=None):
    runtime_su_env = su_env or api.Environment(env.cr, SUPERUSER_ID, dict(env.context or {}))
    try:
        action = None
        if menu_id:
            menu = runtime_su_env["ir.ui.menu"].browse(int(menu_id))
            action = menu.action if menu.exists() else None
        if (not action) and action_id:
            action = runtime_su_env["ir.actions.actions"].browse(int(action_id))
        if action and action.exists():
            return action
    except Exception:
        return None
    return None


def resolve_model_from_entry_context(env, *, su_env=None, menu_id=None, action_id=None) -> str | None:
    action = resolve_entry_action(env, su_env=su_env, menu_id=menu_id, action_id=action_id)
    if not action:
        return None

    try:
        res_model = getattr(action, "res_model", None)
        if not res_model and getattr(action, "_name", "") == "ir.actions.act_window":
            res_model = action.res_model
        if res_model:
            return str(res_model)
    except Exception:
        return None
    return None


def infer_view_types_from_entry_context(
    env,
    *,
    su_env=None,
    menu_id=None,
    action_id=None,
    valid_views: Iterable[str] | None = None,
) -> List[str]:
    action = resolve_entry_action(env, su_env=su_env, menu_id=menu_id, action_id=action_id)
    if not action or getattr(action, "_name", "") != "ir.actions.act_window":
        return []

    try:
        raw_view_mode = (getattr(action, "view_mode", None) or "").strip()
    except Exception:
        return []
    if not raw_view_mode:
        return []

    allowed = set(valid_views or [])
    seen = set()
    resolved: List[str] = []
    for part in raw_view_mode.split(","):
        view_type = str(part or "").strip().lower()
        if not view_type:
            continue
        if allowed and view_type not in allowed:
            continue
        if view_type in seen:
            continue
        seen.add(view_type)
        resolved.append(view_type)
    return resolved


def normalize_requested_view_types(
    view_type_raw: Any,
    *,
    inferred_view_types: Iterable[str] | None = None,
    valid_views: Iterable[str] | None = None,
    default_view_type: str = "tree",
) -> List[str]:
    if isinstance(view_type_raw, (list, tuple)):
        parts = [str(value or "").strip().lower() for value in view_type_raw]
    elif isinstance(view_type_raw, str) and view_type_raw.strip():
        parts = [part for part in re.split(r"[,\s]+", view_type_raw.strip()) if part]
    else:
        parts = [str(value or "").strip().lower() for value in (inferred_view_types or [])]
        if not parts:
            parts = [default_view_type]

    allowed = set(valid_views or [])
    seen = set()
    resolved: List[str] = []
    for part in parts:
        view_type = str(part or "").strip().lower()
        if not view_type:
            continue
        if allowed and view_type not in allowed:
            raise ValueError(f"unsupported view_type: {view_type}")
        if view_type in seen:
            continue
        seen.add(view_type)
        resolved.append(view_type)
    return resolved
