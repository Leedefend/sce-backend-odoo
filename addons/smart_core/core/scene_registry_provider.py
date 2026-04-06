# -*- coding: utf-8 -*-
from __future__ import annotations

def load_scene_configs(env, *, drift=None):
    from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs as direct_load_scene_configs

    payload = direct_load_scene_configs(env, drift=drift)
    return payload if isinstance(payload, list) else []


def has_db_scenes(env) -> bool:
    from odoo.addons.smart_construction_scene.scene_registry import has_db_scenes as direct_has_db_scenes

    return bool(direct_has_db_scenes(env))


def get_scene_version(env) -> str | None:
    from odoo.addons.smart_construction_scene.scene_registry import get_scene_version as direct_get_scene_version

    text = str(direct_get_scene_version() or "").strip()
    return text or None


def get_schema_version(env) -> str | None:
    from odoo.addons.smart_construction_scene.scene_registry import get_schema_version as direct_get_schema_version

    text = str(direct_get_schema_version() or "").strip()
    return text or None
