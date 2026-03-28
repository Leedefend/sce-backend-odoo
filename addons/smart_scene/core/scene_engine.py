# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from .layout_orchestrator import apply_zone_priority
from .scene_contract_builder import build_scene_contract
from .scene_resolver import resolve_scene_identity
from .structure_mapper import map_zone_specs_to_blocks


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _derive_permissions_from_semantic_surface(surface: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = _as_dict(surface)
    permission_surface = _as_dict(payload.get("permission_surface"))
    if not permission_surface:
        return {}
    visible = bool(permission_surface.get("visible", True))
    allowed = bool(permission_surface.get("allowed", True))
    return {
        "can_read": visible and allowed,
        "can_edit": allowed,
    }


def build_scene_contract_from_specs(
    *,
    scene_hint: Dict[str, Any],
    page_hint: Dict[str, Any],
    zone_specs: List[Dict[str, Any]],
    built_zones: Dict[str, Any],
    zone_order: List[str] | None = None,
    record: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
    nav_ref: Dict[str, Any] | None = None,
    semantic_surface: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    resolved = resolve_scene_identity(scene_hint=scene_hint, page_hint=page_hint, semantic_surface=semantic_surface or {})
    mapped_specs = map_zone_specs_to_blocks(zone_specs)
    ordered_specs = apply_zone_priority(mapped_specs, zone_order=zone_order)
    diagnostics_payload = dict(diagnostics or {})
    diagnostics_payload.setdefault("scene_engine", "smart_scene.core.scene_engine")
    diagnostics_payload.setdefault("zone_specs_mapped", ordered_specs)
    derived_permissions = _derive_permissions_from_semantic_surface(semantic_surface)
    return build_scene_contract(
        scene=resolved.get("scene") or {},
        page=resolved.get("page") or {},
        zones=built_zones,
        record=record or {},
        nav_ref=nav_ref or {
            "active_scene_key": str((resolved.get("scene") or {}).get("scene_key") or "").strip(),
            "active_menu_id": page_hint.get("menu_id") if isinstance(page_hint, dict) else None,
        },
        permissions=derived_permissions,
        diagnostics=diagnostics_payload,
        semantic_surface=semantic_surface or {},
    )
