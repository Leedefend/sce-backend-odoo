# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def map_zone_specs_to_blocks(zone_specs: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mapped: List[Dict[str, Any]] = []
    for row in list(zone_specs or []):
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip()
        if not key:
            continue
        mapped.append(
            {
                "key": key,
                "title": str(row.get("title") or key),
                "zone_type": str(row.get("zone_type") or "secondary"),
                "display_mode": str(row.get("display_mode") or "stack"),
                "block_key": str(row.get("block_key") or "").strip(),
            }
        )
    return mapped

