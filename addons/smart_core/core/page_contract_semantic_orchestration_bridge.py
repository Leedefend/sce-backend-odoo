# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _resolve_semantic_page_type(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))

    if view_type == "form":
        return "detail"
    if view_type == "tree":
        return "list"
    if view_type == "kanban":
        return "workspace"
    if view_type == "search":
        return "entry_hub"
    if semantic_page.get("kanban_semantics"):
        return "workspace"
    if semantic_page.get("list_semantics"):
        return "list"
    if semantic_page.get("title_node"):
        return "detail"
    return ""


def _search_filters_from_surface(surface: Dict[str, Any]) -> list[Dict[str, Any]]:
    native_view = _as_dict(surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    filters: list[Dict[str, Any]] = []

    for row in search_view.get("filters") or []:
        if not isinstance(row, dict):
            continue
        filters.append(
            {
                "kind": "filter",
                "key": row.get("name"),
                "label": row.get("string") or row.get("name"),
            }
        )
    for row in search_view.get("group_bys") or []:
        if not isinstance(row, dict):
            continue
        filters.append(
            {
                "kind": "group_by",
                "key": row.get("group_by") or row.get("name"),
                "label": row.get("string") or row.get("name"),
            }
        )
    for row in search_view.get("searchpanel") or []:
        if not isinstance(row, dict):
            continue
        filters.append(
            {
                "kind": "searchpanel",
                "key": row.get("name"),
                "label": row.get("string") or row.get("name"),
            }
        )
    return [row for row in filters if row.get("key")]


def apply_page_contract_semantic_orchestration_bridge(
    orchestration: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(orchestration or {})
    meta = _as_dict(out.get("meta"))
    surface = _as_dict(meta.get("parser_semantic_surface"))
    if not surface:
        return out

    semantic_page_type = _resolve_semantic_page_type(surface)
    if not semantic_page_type:
        return out

    page = _as_dict(out.get("page"))
    page["page_type"] = semantic_page_type
    if semantic_page_type == "workspace":
        page["layout_mode"] = "workspace_flow"
        page["priority_model"] = "role_first"
    elif semantic_page_type == "detail":
        page["layout_mode"] = "detail_focus"
        page["priority_model"] = "record_first"
    elif semantic_page_type == "list":
        page["layout_mode"] = "list_flow"
        page["priority_model"] = "task_first"
    elif semantic_page_type == "entry_hub":
        page["layout_mode"] = "entry_flow"
        page["priority_model"] = "role_first"
    if not isinstance(page.get("filters"), list) or not page.get("filters"):
        page["filters"] = _search_filters_from_surface(surface)
    out["page"] = page

    render_hints = _as_dict(out.get("render_hints"))
    render_hints["semantic_profile"] = semantic_page_type
    render_hints["semantic_page_type"] = semantic_page_type
    if semantic_page_type == "workspace":
        render_hints["preferred_columns"] = 2
    elif semantic_page_type == "detail":
        render_hints["preferred_columns"] = 1
    elif semantic_page_type == "list":
        render_hints["preferred_columns"] = 2
    elif semantic_page_type == "entry_hub":
        render_hints["preferred_columns"] = 1
    out["render_hints"] = render_hints
    return out
