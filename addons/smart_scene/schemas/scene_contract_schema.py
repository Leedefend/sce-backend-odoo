# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple


REQUIRED_TOP_LEVEL = (
    "contract_version",
    "scene",
    "page",
    "nav_ref",
    "zones",
    "blocks",
    "record",
    "permissions",
    "actions",
    "extensions",
    "diagnostics",
)


def check_top_level_shape(payload: dict) -> Tuple[bool, Dict[str, object]]:
    if not isinstance(payload, dict):
        return False, {"code": "contract_not_dict"}
    missing = [key for key in REQUIRED_TOP_LEVEL if key not in payload]
    if missing:
        return False, {"code": "missing_top_level", "keys": missing}
    if payload.get("contract_version") != "v1":
        return False, {"code": "invalid_contract_version", "value": payload.get("contract_version")}
    if not isinstance(payload.get("actions"), dict):
        return False, {"code": "actions_not_object"}
    if not isinstance(payload.get("permissions"), dict):
        return False, {"code": "permissions_not_object"}
    if not isinstance(payload.get("extensions"), dict):
        return False, {"code": "extensions_not_object"}
    if not isinstance(payload.get("nav_ref"), dict):
        return False, {"code": "nav_ref_not_object"}
    if not isinstance(payload.get("diagnostics"), dict):
        return False, {"code": "diagnostics_not_object"}

    actions = payload.get("actions") if isinstance(payload.get("actions"), dict) else {}
    action_groups = ("primary_actions", "secondary_actions", "contextual_actions", "danger_actions", "recommended_actions")
    for key in action_groups:
        if not isinstance(actions.get(key), list):
            return False, {"code": "invalid_action_group", "group": key}

    permissions = payload.get("permissions") if isinstance(payload.get("permissions"), dict) else {}
    for key in ("can_read", "can_edit", "can_create", "can_delete"):
        if key in permissions and not isinstance(permissions.get(key), bool):
            return False, {"code": "invalid_permission_flag", "flag": key}

    extensions = payload.get("extensions") if isinstance(payload.get("extensions"), dict) else {}
    for key in ("injected_blocks", "injected_actions", "providers"):
        if key in extensions and not isinstance(extensions.get(key), list):
            return False, {"code": "invalid_extensions_group", "group": key}

    nav_ref = payload.get("nav_ref") if isinstance(payload.get("nav_ref"), dict) else {}
    if "active_scene_key" in nav_ref and not isinstance(nav_ref.get("active_scene_key"), str):
        return False, {"code": "invalid_nav_ref_active_scene_key"}
    if "active_menu_key" in nav_ref and not isinstance(nav_ref.get("active_menu_key"), str):
        return False, {"code": "invalid_nav_ref_active_menu_key"}
    active_menu_id = nav_ref.get("active_menu_id")
    if active_menu_id is not None and not isinstance(active_menu_id, int):
        return False, {"code": "invalid_nav_ref_active_menu_id"}

    diagnostics = payload.get("diagnostics") if isinstance(payload.get("diagnostics"), dict) else {}
    if "semantic_runtime_state" in diagnostics and not isinstance(diagnostics.get("semantic_runtime_state"), dict):
        return False, {"code": "invalid_diagnostics_semantic_runtime_state"}
    if "consumer_runtime" in diagnostics and not isinstance(diagnostics.get("consumer_runtime"), dict):
        return False, {"code": "invalid_diagnostics_consumer_runtime"}
    return True, {"code": "ok"}
