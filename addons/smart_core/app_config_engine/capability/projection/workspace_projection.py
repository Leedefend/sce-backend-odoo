# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .capability_runtime_exposure import resolve_primary_intent, resolve_runtime_target


def build_workspace_projection(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tiles: List[Dict[str, Any]] = []
    for row in rows:
        identity = row.get("identity") if isinstance(row, dict) else {}
        ui = row.get("ui") if isinstance(row, dict) else {}
        if not isinstance(identity, dict):
            continue
        key = str(identity.get("key") or "").strip()
        if not key:
            continue
        primary_intent = resolve_primary_intent(row)
        runtime_target = resolve_runtime_target(row)
        tiles.append(
            {
                "key": key,
                "label": str((ui or {}).get("label") or identity.get("name") or "").strip(),
                "group_key": str((ui or {}).get("group_key") or "").strip(),
                "primary_intent": primary_intent,
                "runtime_target": runtime_target,
            }
        )
    return tiles
