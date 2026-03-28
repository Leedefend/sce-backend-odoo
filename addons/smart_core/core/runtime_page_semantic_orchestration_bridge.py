# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _search_filters_from_surface(surface: Dict[str, Any]) -> list[Dict[str, Any]]:
    native_view = _as_dict(surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    filters: list[Dict[str, Any]] = []
    for row in _as_list(search_view.get("filters")):
        if not isinstance(row, dict):
            continue
        filters.append({"kind": "filter", "key": row.get("name"), "label": row.get("string") or row.get("name")})
    for row in _as_list(search_view.get("group_bys")):
        if not isinstance(row, dict):
            continue
        filters.append({"kind": "group_by", "key": row.get("group_by") or row.get("name"), "label": row.get("string") or row.get("name")})
    return [row for row in filters if row.get("key")]


def _search_actions_from_surface(surface: Dict[str, Any]) -> list[Dict[str, Any]]:
    native_view = _as_dict(surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    has_filters = bool(search_view.get("filters"))
    has_group_bys = bool(search_view.get("group_bys"))
    if not (has_filters or has_group_bys):
        return []
    actions: list[Dict[str, Any]] = [
        {"key": "apply_filters", "label": "应用筛选", "intent": "ui.contract"},
    ]
    actions.append({"key": "reset_filters", "label": "重置筛选", "intent": "ui.contract"})
    return actions


def _search_mode_from_surface(surface: Dict[str, Any]) -> str:
    native_view = _as_dict(surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    if _as_list(search_view.get("searchpanel")):
        return "faceted"
    if _as_list(search_view.get("filters")) or _as_list(search_view.get("group_bys")):
        return "filter_bar"
    return ""


def apply_runtime_page_semantic_orchestration_bridge(
    page_payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    page = dict(page_payload or {})
    surface = _as_dict(page.get("runtime_semantic_surface"))
    if not surface:
        return page

    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))

    runtime_context = _as_dict(page.get("runtime_context"))
    if view_type:
        runtime_context["runtime_mode"] = {
            "form": "record_focus",
            "tree": "list_focus",
            "kanban": "board_focus",
            "search": "search_focus",
        }.get(view_type, "generic_focus")
    search_mode = _search_mode_from_surface(surface)
    if search_mode:
        runtime_context["search_mode"] = search_mode
    page["runtime_context"] = runtime_context

    orchestration = _as_dict(page.get("page_orchestration_v1"))
    render_hints = _as_dict(orchestration.get("render_hints"))
    if view_type == "form":
        render_hints["runtime_preferred_columns"] = 1
    elif view_type in {"tree", "kanban"}:
        render_hints["runtime_preferred_columns"] = 2
    else:
        render_hints["runtime_preferred_columns"] = 1
    if semantic_page:
        render_hints["runtime_semantic_page"] = semantic_page
    if search_mode:
        render_hints["runtime_search_profile"] = search_mode
    orchestration["render_hints"] = render_hints

    page_node = _as_dict(orchestration.get("page"))
    if not _as_list(page_node.get("filters")):
        page_node["filters"] = _search_filters_from_surface(surface)
    semantic_actions = _search_actions_from_surface(surface)
    if semantic_actions:
        page_node["global_actions"] = semantic_actions
    orchestration["page"] = page_node

    page["page_orchestration_v1"] = orchestration
    return page
