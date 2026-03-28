# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

WORKSPACE_COLLECTION_KEYS = (
    "task_items",
    "payment_requests",
    "risk_actions",
    "project_actions",
)


def collect_workspace_collections(
    data: dict[str, Any],
    *,
    keys: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    requested = {str(item or "").strip() for item in (keys or []) if str(item or "").strip()}
    collections: dict[str, list[dict[str, Any]]] = {}
    for key in WORKSPACE_COLLECTION_KEYS:
        if requested and key not in requested:
            continue
        rows = data.get(key)
        if isinstance(rows, list):
            collections[key] = [row for row in rows if isinstance(row, dict)]
    return collections
