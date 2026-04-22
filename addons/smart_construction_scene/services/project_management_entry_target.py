# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from odoo.addons.smart_construction_scene.scene_registry import load_scene_configs


PROJECT_MANAGEMENT_SCENE_KEY = "project.management"
PROJECT_MANAGEMENT_ROUTE_FALLBACK = "/s/project.management"


def resolve_project_management_entry_target(env) -> Dict[str, Any]:
    for scene in load_scene_configs(env) or []:
        if not isinstance(scene, dict):
            continue
        if str(scene.get("code") or "").strip() != PROJECT_MANAGEMENT_SCENE_KEY:
            continue
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        route = str(target.get("route") or "").strip()
        if route:
            return {
                "scene_key": PROJECT_MANAGEMENT_SCENE_KEY,
                "route": route,
                "target": dict(target),
            }
    return {
        "scene_key": PROJECT_MANAGEMENT_SCENE_KEY,
        "route": PROJECT_MANAGEMENT_ROUTE_FALLBACK,
        "target": {"route": PROJECT_MANAGEMENT_ROUTE_FALLBACK},
    }
