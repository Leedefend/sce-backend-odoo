# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict

from .scene_parser_semantic_bridge import apply_scene_parser_semantic_bridge


REQUIRED_TOP_LEVEL_KEYS = (
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


def _synthetic_menu_id(key: str, base: int = 700_000_000, span: int = 200_000_000) -> int:
    import zlib

    raw = zlib.crc32(str(key or "").encode("utf-8")) & 0xFFFFFFFF
    return int(base + (raw % span))


def _normalize_nav_ref(
    nav_ref: Dict[str, Any] | None,
    *,
    scene: Dict[str, Any],
    page: Dict[str, Any],
    diagnostics: Dict[str, Any] | None,
) -> Dict[str, Any]:
    payload = dict(nav_ref or {})
    diagnostics_payload = dict(diagnostics or {})
    scene_key = str(
        payload.get("active_scene_key")
        or scene.get("scene_key")
        or scene.get("key")
        or scene.get("code")
        or ""
    ).strip()
    active_menu_id = payload.get("active_menu_id")
    if active_menu_id is None:
        active_menu_id = page.get("menu_id")
    if active_menu_id is None:
        active_menu_id = diagnostics_payload.get("active_menu_id")
    if active_menu_id is None and scene_key:
        active_menu_id = _synthetic_menu_id(f"scene:{scene_key}")
    return {
        "active_scene_key": scene_key,
        "active_menu_id": int(active_menu_id) if isinstance(active_menu_id, int) or str(active_menu_id).isdigit() else None,
        "active_menu_key": str(payload.get("active_menu_key") or (f"scene:{scene_key}" if scene_key else "")).strip(),
    }


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


def _normalize_permissions(permissions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(permissions or {})
    return {
        "can_read": bool(payload.get("can_read", True)),
        "can_edit": bool(payload.get("can_edit", True)),
        "can_create": bool(payload.get("can_create", False)),
        "can_delete": bool(payload.get("can_delete", False)),
        "disabled_actions": dict(payload.get("disabled_actions") or {}),
        "record_state_summary": dict(payload.get("record_state_summary") or {}),
    }


def _normalize_extensions(extensions: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(extensions or {})
    return {
        "injected_blocks": list(payload.get("injected_blocks") or []),
        "injected_actions": list(payload.get("injected_actions") or []),
        "providers": list(payload.get("providers") or []),
    }


def _normalize_diagnostics(diagnostics: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = dict(diagnostics or {})
    payload.setdefault("trace_id", str(payload.get("trace_id") or ""))
    payload.setdefault("source_versions", {})
    payload.setdefault("build_pipeline", ["scene_resolver", "structure_mapper", "layout_orchestrator", "scene_contract_builder"])
    payload.setdefault("warnings", [])
    payload.setdefault("semantic_runtime_state", {})
    return payload


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
    nav_ref: Dict[str, Any] | None = None,
    permissions: Dict[str, Any] | None = None,
    actions: Dict[str, Any] | None = None,
    extensions: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
    semantic_surface: Dict[str, Any] | None = None,
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
        "nav_ref": _normalize_nav_ref(nav_ref, scene=normalized_scene, page=normalized_page, diagnostics=diagnostics),
        "zones": dict(zones or {}),
        "zones_v1": zone_rows,
        "blocks": block_rows,
        "record": dict(record or {}),
        "permissions": _normalize_permissions(permissions),
        "actions": _normalize_actions(actions),
        "extensions": _normalize_extensions(extensions),
        "diagnostics": _normalize_diagnostics(diagnostics),
    }
    contract["scene_contract_v1"] = {
        "contract_version": "v1",
        "scene": dict(contract["scene"]),
        "page": dict(contract["page"]),
        "nav_ref": dict(contract["nav_ref"]),
        "zones": list(contract["zones_v1"]),
        "blocks": dict(contract["blocks"]),
        "actions": dict(contract["actions"]),
        "permissions": dict(contract["permissions"]),
        "record": dict(contract["record"]),
        "extensions": dict(contract["extensions"]),
        "diagnostics": dict(contract["diagnostics"]),
    }
    contract = apply_scene_parser_semantic_bridge(contract, semantic_surface)
    verdict = validate_scene_contract_shape(contract)
    contract["diagnostics"]["scene_contract_shape"] = verdict
    return contract
