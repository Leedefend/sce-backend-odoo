# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


def resolve_builtin_surface_nav_allowlist(env=None, *, hook: Callable[[Any, str, Any], Any] | None = None, default_map: dict | None = None) -> dict:
    payload = hook(env, "smart_core_surface_nav_allowlist", env) if callable(hook) else None
    if isinstance(payload, dict):
        return payload
    return dict(default_map or {})


def resolve_builtin_surface_deep_link_allowlist(env=None, *, hook: Callable[[Any, str, Any], Any] | None = None, default_map: dict | None = None) -> dict:
    payload = hook(env, "smart_core_surface_deep_link_allowlist", env) if callable(hook) else None
    if isinstance(payload, dict):
        return payload
    return dict(default_map or {})


def resolve_surface_policy_default_name(env=None, *, hook: Callable[[Any, str, Any], Any] | None = None, default_name: str = "") -> str:
    payload = hook(env, "smart_core_surface_policy_default_name", env) if callable(hook) else None
    value = str(payload or "").strip()
    return value or default_name
