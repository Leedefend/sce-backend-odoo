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
    scene_type = str(scene_row.get("scene_type") or fallback.get("scene_type") or "").strip()
    layout_mode = str(scene_row.get("layout_mode") or fallback.get("layout_mode") or "").strip()
    page_goal = str(scene_row.get("page_goal") or fallback.get("page_goal") or "").strip()
    interaction_mode = str(scene_row.get("interaction_mode") or fallback.get("interaction_mode") or "").strip()
    scene_version = str(scene_row.get("scene_version") or fallback.get("scene_version") or "").strip()

    model_name = str(page_row.get("model") or fallback.get("model") or "").strip()
    view_type = str(page_row.get("view_type") or fallback.get("view_type") or "").strip()
    title_field = str(page_row.get("title_field") or fallback.get("title_field") or "").strip()
    page_status = str(page_row.get("page_status") or fallback.get("page_status") or "").strip()
    record_id = page_row.get("record_id") if isinstance(page_row, dict) else None

    return {
        "scene": {
            "key": scene_key,
            "page": page_key,
            "scene_key": scene_key,
            "scene_type": scene_type,
            "layout_mode": layout_mode,
            "page_goal": page_goal,
            "interaction_mode": interaction_mode,
            "scene_version": scene_version,
        },
        "page": {
            "key": page_key,
            "title": str(page_row.get("title") or fallback.get("page_title") or "").strip(),
            "route": page_route,
            "model": model_name,
            "view_type": view_type,
            "title_field": title_field,
            "page_status": page_status,
            "record_id": record_id,
        },
    }
