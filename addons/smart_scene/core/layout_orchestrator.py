# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def apply_zone_priority(zones: Iterable[Dict[str, Any]], zone_order: List[str] | None = None) -> List[Dict[str, Any]]:
    rows = [dict(row) for row in list(zones or []) if isinstance(row, dict)]
    order = [str(key).strip() for key in (zone_order or []) if str(key).strip()]
    if not order:
        return rows
    priority_map = {key: 100 - (idx * 10) for idx, key in enumerate(order)}
    for row in rows:
        key = str(row.get("key") or "").strip()
        if key in priority_map:
            row["priority"] = priority_map[key]
    return rows

