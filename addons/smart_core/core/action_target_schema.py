# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def scene_target(scene_key: str) -> Dict[str, Any]:
    return {"kind": "scene.key", "scene_key": str(scene_key or "").strip()}


def route_path_target(path: str) -> Dict[str, Any]:
    return {"kind": "route.path", "path": str(path or "").strip()}


def page_refresh_target() -> Dict[str, Any]:
    return {"kind": "page.refresh"}


def menu_first_reachable_target() -> Dict[str, Any]:
    return {"kind": "menu.first_reachable"}


def resolve_action_target(action_key: str, page_key: str) -> Dict[str, Any]:
    key = str(action_key or "").strip().lower()
    page = str(page_key or "").strip().lower()
    if key == "open_risk_dashboard":
        return scene_target("workspace.home")
    if key == "open_my_work":
        return scene_target("my_work.workspace")
    if key == "apply_filters":
        return scene_target(page)
    if key == "open_list":
        if page in {"usage_analytics", "scene_health"}:
            return scene_target(page)
        return scene_target("workspace.home")
    if key == "open_workbench":
        return scene_target("workspace.home")
    if key == "open_workspace_overview":
        return scene_target("workspace.home")
    if key == "open_menu":
        return menu_first_reachable_target()
    if key in {"refresh_page", "refresh"}:
        return page_refresh_target()
    if key == "open_usage_analytics":
        return route_path_target("/admin/usage-analytics")
    if key == "open_landing":
        return scene_target("workspace.home")
    if key == "open_scene":
        return scene_target("workspace.home")
    return scene_target(page)
