# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from .layout_orchestrator import apply_zone_priority
from .scene_contract_builder import build_scene_contract
from .scene_resolver import resolve_scene_identity
from .structure_mapper import map_zone_specs_to_blocks


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
) -> Dict[str, Any]:
    resolved = resolve_scene_identity(scene_hint=scene_hint, page_hint=page_hint)
    mapped_specs = map_zone_specs_to_blocks(zone_specs)
    ordered_specs = apply_zone_priority(mapped_specs, zone_order=zone_order)
    diagnostics_payload = dict(diagnostics or {})
    diagnostics_payload.setdefault("scene_engine", "smart_scene.core.scene_engine")
    diagnostics_payload.setdefault("zone_specs_mapped", ordered_specs)
    return build_scene_contract(
        scene=resolved.get("scene") or {},
        page=resolved.get("page") or {},
        zones=built_zones,
        record=record or {},
        nav_ref=nav_ref or {
            "active_scene_key": str((resolved.get("scene") or {}).get("scene_key") or "").strip(),
            "active_menu_id": page_hint.get("menu_id") if isinstance(page_hint, dict) else None,
        },
        diagnostics=diagnostics_payload,
    )
