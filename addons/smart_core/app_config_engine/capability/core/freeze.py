# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable, List


def build_registry_snapshot(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    snapshot: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            snapshot.append(dict(row))
    snapshot.sort(key=lambda item: str((item.get("identity") or {}).get("key") or ""))
    return snapshot
