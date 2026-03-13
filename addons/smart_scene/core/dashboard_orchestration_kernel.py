# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def build_single_block_zones(
    zone_specs: Iterable[Dict[str, Any]],
    builder_map: Dict[str, Any],
    project: Any,
    context: Dict[str, Any],
    fallback_error_block,
) -> Dict[str, Dict[str, Any]]:
    zones: Dict[str, Dict[str, Any]] = {}
    for spec in list(zone_specs):
        key = str(spec.get("key") or "").strip()
        if not key:
            continue
        block_key = str(spec.get("block_key") or "").strip()
        builder = builder_map.get(block_key)
        block = (
            builder.build(project=project, context=context)
            if builder
            else fallback_error_block(block_key or ("block.%s" % key), "BLOCK_BUILDER_NOT_FOUND")
        )
        zones[key] = {
            "zone_key": str(spec.get("zone_key") or ("zone.%s" % key)),
            "title": str(spec.get("title") or key),
            "zone_type": str(spec.get("zone_type") or "secondary"),
            "display_mode": str(spec.get("display_mode") or "stack"),
            "blocks": [block],
        }
    return zones

