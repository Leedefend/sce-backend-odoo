# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_scene(item: Dict[str, Any]) -> Dict[str, Any]:
    scene_key = _text(item.get("code") or item.get("key"))
    scene_title = _text(item.get("name") or scene_key)
    layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
    return {
        "key": scene_key,
        "title": scene_title,
        "layout": dict(layout),
    }


def _normalize_actions(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    target = item.get("target") if isinstance(item.get("target"), dict) else {}
    out: List[Dict[str, Any]] = []
    action_id = int(target.get("action_id") or 0)
    menu_id = int(target.get("menu_id") or 0)
    route = _text(target.get("route"))
    if action_id > 0:
        out.append(
            {
                "key": "open_scene_action",
                "label": "打开场景",
                "intent": "ui.contract",
                "target": {
                    "action_id": action_id,
                    "menu_id": menu_id if menu_id > 0 else None,
                },
            }
        )
    if route:
        out.append(
            {
                "key": "open_scene_route",
                "label": "打开路由",
                "intent": "ui.contract",
                "target": {"route": route},
            }
        )
    return out


def _normalize_search_surface(item: Dict[str, Any]) -> Dict[str, Any]:
    list_profile = item.get("list_profile") if isinstance(item.get("list_profile"), dict) else {}
    return {
        "default_sort": _text(item.get("default_sort")),
        "filters": list(item.get("filters") or []),
        "columns": list(list_profile.get("columns") or []),
        "hidden_columns": list(list_profile.get("hidden_columns") or []),
    }


def _normalize_permission_surface(item: Dict[str, Any]) -> Dict[str, Any]:
    access = item.get("access") if isinstance(item.get("access"), dict) else {}
    required = access.get("required_capabilities")
    return {
        "visible": bool(access.get("visible", True)),
        "allowed": bool(access.get("allowed", True)),
        "reason_code": _text(access.get("reason_code")),
        "required_capabilities": list(required) if isinstance(required, list) else [],
    }


def _scene_ready_entry(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized_scene = _normalize_scene(item)
    scene_key = _text(normalized_scene.get("key"))
    scene_route = _text(((item.get("target") or {}) if isinstance(item.get("target"), dict) else {}).get("route"))
    if not scene_route and scene_key:
        scene_route = f"/s/{scene_key}"
    return {
        "scene": normalized_scene,
        "page": {
            "scene_key": scene_key,
            "route": scene_route,
            "zones": [
                {"name": "header", "blocks": ["scene.header"]},
                {"name": "main", "blocks": ["scene.main"]},
            ],
        },
        "actions": _normalize_actions(item),
        "search_surface": _normalize_search_surface(item),
        "workflow_surface": {},
        "permission_surface": _normalize_permission_surface(item),
        "meta": {
            "target": dict(item.get("target") or {}),
            "tiles": list(item.get("tiles") or []),
        },
    }


def build_scene_ready_contract_v1(
    *,
    scenes: List[Dict[str, Any]] | None,
    role_surface: Dict[str, Any] | None = None,
    scene_version: str | None = None,
    schema_version: str | None = None,
    scene_channel: str | None = None,
) -> Dict[str, Any]:
    scene_rows = []
    for item in scenes or []:
        if not isinstance(item, dict):
            continue
        scene_key = _text(item.get("code") or item.get("key"))
        if not scene_key:
            continue
        scene_rows.append(item)
    scene_rows.sort(key=lambda row: _text(row.get("code") or row.get("key")))

    entries = [_scene_ready_entry(row) for row in scene_rows]
    role_payload = role_surface if isinstance(role_surface, dict) else {}
    landing_scene_key = _text(role_payload.get("landing_scene_key"))
    if not landing_scene_key and entries:
        landing_scene_key = _text((entries[0].get("scene") or {}).get("key"))

    return {
        "contract_version": "v1",
        "schema_version": "scene_ready_contract_v1",
        "scene_version": _text(scene_version),
        "source_schema_version": _text(schema_version),
        "scene_channel": _text(scene_channel),
        "active_scene_key": landing_scene_key,
        "scenes": entries,
        "meta": {
            "generated_by": "smart_core.scene_ready_contract_builder",
            "scene_count": len(entries),
            "mode": "dual_track",
        },
    }
