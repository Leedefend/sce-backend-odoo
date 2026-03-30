# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_filter_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        item = {
            "key": _text(row.get("name")),
            "name": _text(row.get("name")),
            "label": _text(row.get("string") or row.get("label") or row.get("name")),
            "kind": "filter",
            "domain": row.get("domain"),
            "context": _as_dict(row.get("context")),
        }
        if item["key"]:
            out.append(item)
    return out


def _normalize_group_by_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        field = _text(row.get("field") or row.get("group_by") or row.get("name"))
        item = {
            "key": field or _text(row.get("name")),
            "name": _text(row.get("name")),
            "field": field,
            "label": _text(row.get("string") or row.get("label") or field or row.get("name")),
            "kind": "group_by",
            "context": _as_dict(row.get("context")),
        }
        if item["key"] and item["field"]:
            out.append(item)
    return out


def _normalize_searchpanel_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = _text(row.get("name"))
        select = _text(row.get("select"))
        item = {
            "key": name,
            "name": name,
            "label": _text(row.get("string") or row.get("label") or name),
            "kind": "searchpanel",
            "select": select or "single",
            "multi": select == "multi" or bool(_as_dict(row.get("semantic_meta")).get("is_multi")),
            "icon": _text(row.get("icon")),
        }
        if name:
            out.append(item)
    return out


def _normalize_default_state(search_surface: Dict[str, Any]) -> Dict[str, Any]:
    raw = _as_dict(search_surface.get("default_state"))
    filters = _normalize_filter_rows(_as_list(raw.get("filters")))
    group_by = _normalize_group_by_rows(_as_list(raw.get("group_by")))
    searchpanel = _normalize_searchpanel_rows(_as_list(raw.get("searchpanel")))
    out: Dict[str, Any] = {}
    if filters:
        out["filters"] = filters
    if group_by:
        out["group_by"] = group_by
    if searchpanel:
        out["searchpanel"] = searchpanel
    return out


def _search_mode(search_view: Dict[str, Any]) -> str:
    if _as_list(search_view.get("searchpanel")):
        return "faceted"
    if _as_list(search_view.get("filters")) or _as_list(search_view.get("group_bys")):
        return "filter_bar"
    return ""


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
        search_surface["group_by"] = _as_list(search_view.get("group_bys"))
    if not _as_list(search_surface.get("searchpanel")):
        search_surface["searchpanel"] = _as_list(search_view.get("searchpanel"))
    search_surface["filters"] = _normalize_filter_rows(_as_list(search_surface.get("filters")))
    search_surface["group_by"] = _normalize_group_by_rows(_as_list(search_surface.get("group_by")))
    search_surface["searchpanel"] = _normalize_searchpanel_rows(_as_list(search_surface.get("searchpanel")))
    default_state = _normalize_default_state(search_surface)
    if default_state:
        search_surface["default_state"] = default_state
    mode = _search_mode(search_view)
    if mode:
        search_surface["mode"] = mode
    if search_surface:
        out["search_surface"] = search_surface
    return out
