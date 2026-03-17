# -*- coding: utf-8 -*-
from __future__ import annotations


def resolve_scene_policy(scene_key: str, role_code: str = "") -> dict:
    normalized_scene = str(scene_key or "").strip()
    normalized_role = str(role_code or "").strip().lower()

    policy = {
        "scene_key": normalized_scene,
        "action_visibility": "default",
        "search_limit": 8,
    }
    if normalized_scene == "projects.intake":
        policy["next_scene_on_success"] = "project.management"
    elif normalized_scene == "projects.list":
        policy["next_scene_on_primary"] = "projects.intake"

    if normalized_role in {"project_manager", "pm"}:
        policy["action_visibility"] = "manager"
    return policy

