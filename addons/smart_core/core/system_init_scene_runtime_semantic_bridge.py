# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _resolve_scene_key(row: Dict[str, Any]) -> str:
    scene = _as_dict(row.get("scene"))
    page = _as_dict(row.get("page"))
    page_ctx = _as_dict(page.get("context"))
    return _text(
        scene.get("key")
        or row.get("scene_key")
        or page_ctx.get("scene_key")
        or page_ctx.get("page_key")
    )


def _pick_semantic_row(rows: List[Dict[str, Any]], active_scene_key: str) -> Dict[str, Any]:
    normalized_active = _text(active_scene_key)
    if normalized_active:
        for row in rows:
            if _resolve_scene_key(row) == normalized_active:
                return row
    for row in rows:
        if any(
            (
                _as_dict(row.get("parser_semantic_surface")),
                _as_dict(row.get("semantic_view")),
                _as_dict(row.get("semantic_page")),
                _text(row.get("view_type")),
            )
        ):
            return row
    return rows[0] if rows else {}


def apply_system_init_scene_runtime_semantic_bridge(
    data: Dict[str, Any] | None,
    *,
    active_scene_key: str = "",
) -> Dict[str, Any]:
    out = dict(data or {})
    scene_ready = _as_dict(out.get("scene_ready_contract_v1"))
    rows = [row for row in _as_list(scene_ready.get("scenes")) if isinstance(row, dict)]
    if not rows:
        return out

    row = _pick_semantic_row(rows, active_scene_key or _text(scene_ready.get("active_scene_key")))
    if not row:
        return out

    parser_surface = _as_dict(row.get("parser_semantic_surface"))
    semantic_view = _as_dict(row.get("semantic_view"))
    semantic_page = _as_dict(row.get("semantic_page"))
    view_type = _text(
        row.get("view_type")
        or _as_dict(_as_dict(parser_surface).get("parser_contract")).get("view_type")
        or _as_dict(_as_dict(_as_dict(row.get("page")).get("context"))).get("view_type")
    )
    scene_key = _resolve_scene_key(row)

    if not (parser_surface or semantic_view or semantic_page or view_type):
        return out

    out["semantic_runtime"] = {
        "scene_key": scene_key,
        "view_type": view_type,
        "semantic_view": semantic_view,
        "semantic_page": semantic_page,
        "parser_semantic_surface": parser_surface,
    }
    out["released_scene_semantic_surface"] = {
        "scene_key": scene_key,
        "parser_semantic_surface": parser_surface,
        "page_surface": {
            "view_type": view_type,
            "semantic_view": semantic_view,
            "semantic_page": semantic_page,
        },
    }

    nav_meta = _as_dict(out.get("nav_meta"))
    if nav_meta:
        nav_meta["semantic_scene_key"] = scene_key
        nav_meta["semantic_view_type"] = view_type
        nav_meta["semantic_source_view"] = _text(semantic_view.get("source_view"))
        out["nav_meta"] = nav_meta
    return out
