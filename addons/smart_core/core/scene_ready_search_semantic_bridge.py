# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _project_group_by(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = {
            "field": row.get("group_by") or row.get("name"),
            "label": row.get("string") or row.get("name"),
        }
        if item["field"]:
            out.append(item)
    return out


def apply_scene_ready_search_semantic_bridge(
    payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    parser_surface = _as_dict(out.get("parser_semantic_surface"))
    if not parser_surface:
        parser_surface = _as_dict(_as_dict(out.get("meta")).get("parser_semantic_surface"))
    if not parser_surface:
        return out

    native_view = _as_dict(parser_surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    if not search_view:
        return out

    search_surface = _as_dict(out.get("search_surface"))
    if not _as_list(search_surface.get("fields")):
        search_surface["fields"] = _as_list(search_view.get("fields"))
    if not _as_list(search_surface.get("filters")):
        search_surface["filters"] = _as_list(search_view.get("filters"))
    if not _as_list(search_surface.get("group_by")):
        search_surface["group_by"] = _project_group_by(_as_list(search_view.get("group_bys")))
    if not _as_list(search_surface.get("searchpanel")):
        search_surface["searchpanel"] = _as_list(search_view.get("searchpanel"))
    if search_surface:
        out["search_surface"] = search_surface
    return out
