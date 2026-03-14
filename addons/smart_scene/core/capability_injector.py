# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def inject_extension_blocks(
    *,
    zones: Dict[str, Dict[str, Any]],
    extension_blocks: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Dict[str, Any]]:
    out = {key: dict(value) for key, value in (zones or {}).items()}
    for block in list(extension_blocks or []):
        if not isinstance(block, dict):
            continue
        zone_key = str(block.get("zone_key") or "").strip()
        if not zone_key or zone_key not in out:
            continue
        zone_row = out[zone_key]
        blocks = list(zone_row.get("blocks") or [])
        blocks.append(dict(block))
        zone_row["blocks"] = blocks
        out[zone_key] = zone_row
    return out

