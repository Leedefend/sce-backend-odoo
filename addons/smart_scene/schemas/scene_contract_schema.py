# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, Tuple


REQUIRED_TOP_LEVEL = (
    "contract_version",
    "scene",
    "page",
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
    return True, {"code": "ok"}
