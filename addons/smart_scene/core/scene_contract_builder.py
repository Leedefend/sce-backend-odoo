# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


REQUIRED_TOP_LEVEL_KEYS = (
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


def _normalize_zones_and_blocks(zones: Dict[str, Any]) -> tuple[list[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    zone_rows = []
    blocks: Dict[str, Dict[str, Any]] = {}
    if not isinstance(zones, dict):
        return zone_rows, blocks

    for zone_key, zone in zones.items():
        if not isinstance(zone, dict):
            continue
        normalized_zone_key = str(zone.get("zone_key") or zone_key or "").strip()
        if not normalized_zone_key:
            continue
        block_keys = []
        block_rows = zone.get("blocks") if isinstance(zone.get("blocks"), list) else []
        for index, block in enumerate(block_rows):
            if not isinstance(block, dict):
                continue
            block_key = str(block.get("block_key") or block.get("key") or f"{normalized_zone_key}.block.{index}").strip()
            if not block_key:
                continue
            block_keys.append(block_key)
            if block_key not in blocks:
                blocks[block_key] = dict(block)

        zone_rows.append(
            {
                "key": normalized_zone_key,
                "title": str(zone.get("title") or normalized_zone_key),
                "zone_type": str(zone.get("zone_type") or "secondary"),
                "display_mode": str(zone.get("display_mode") or "stack"),
                "block_keys": block_keys,
                "priority": int(zone.get("priority") or 0),
            }
        )

    return zone_rows, blocks


def _normalize_actions(actions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(actions or {})
    action_groups = {
        "primary_actions": list(payload.get("primary_actions") or []),
        "secondary_actions": list(payload.get("secondary_actions") or []),
        "contextual_actions": list(payload.get("contextual_actions") or []),
        "danger_actions": list(payload.get("danger_actions") or []),
        "recommended_actions": list(payload.get("recommended_actions") or []),
    }
    return action_groups


def validate_scene_contract_shape(contract: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not isinstance(contract, dict):
        return {"ok": False, "issues": [{"code": "contract_not_dict"}]}
    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in contract:
            issues.append({"code": "missing_key", "key": key})
    return {"ok": len(issues) == 0, "issues": issues}


def build_scene_contract(
    *,
    scene: Dict[str, Any],
    page: Dict[str, Any],
    zones: Dict[str, Any],
    record: Dict[str, Any] | None = None,
    permissions: Dict[str, Any] | None = None,
    actions: Dict[str, Any] | None = None,
    extensions: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    zone_rows, block_rows = _normalize_zones_and_blocks(dict(zones or {}))
    normalized_scene = dict(scene or {})
    normalized_page = dict(page or {})

    if "scene_key" not in normalized_scene:
        normalized_scene["scene_key"] = str(normalized_scene.get("key") or "").strip()
    if "record_id" not in normalized_page:
        normalized_page["record_id"] = None

    contract = {
        "contract_version": "v1",
        "scene": normalized_scene,
        "page": normalized_page,
        "zones": dict(zones or {}),
        "zones_v1": zone_rows,
        "blocks": block_rows,
        "record": dict(record or {}),
        "permissions": dict(permissions or {}),
        "actions": _normalize_actions(actions),
        "extensions": dict(extensions or {}),
        "diagnostics": dict(diagnostics or {}),
    }
    verdict = validate_scene_contract_shape(contract)
    contract["diagnostics"]["scene_contract_shape"] = verdict
    return contract
