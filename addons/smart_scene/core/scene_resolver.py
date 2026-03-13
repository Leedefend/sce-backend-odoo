# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def resolve_scene_identity(
    *,
    scene_hint: Dict[str, Any] | None,
    page_hint: Dict[str, Any] | None,
    defaults: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    fallback = defaults or {}
    scene_row = scene_hint or {}
    page_row = page_hint or {}
    scene_key = str(scene_row.get("key") or fallback.get("scene_key") or "").strip()
    page_key = str(page_row.get("key") or scene_row.get("page") or fallback.get("page_key") or "").strip()
    page_route = str(page_row.get("route") or fallback.get("page_route") or "").strip()
    return {
        "scene": {
            "key": scene_key,
            "page": page_key,
        },
        "page": {
            "key": page_key,
            "title": str(page_row.get("title") or fallback.get("page_title") or "").strip(),
            "route": page_route,
        },
    }

