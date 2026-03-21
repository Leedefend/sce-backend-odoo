# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_core.utils.extension_hooks import call_extension_hook_first


def load_scene_configs(env, *, drift=None):
    payload = call_extension_hook_first(env, "smart_core_load_scene_configs", env, drift=drift)
    return payload if isinstance(payload, list) else []


def has_db_scenes(env) -> bool:
    result = call_extension_hook_first(env, "smart_core_has_db_scenes", env)
    return bool(result)


def get_scene_version(env) -> str | None:
    result = call_extension_hook_first(env, "smart_core_get_scene_version", env)
    text = str(result or "").strip()
    return text or None


def get_schema_version(env) -> str | None:
    result = call_extension_hook_first(env, "smart_core_get_schema_version", env)
    text = str(result or "").strip()
    return text or None
