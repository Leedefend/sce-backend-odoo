# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _semantic_layout_mode(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))
    if view_type == "form":
        return "detail_focus"
    if view_type == "tree":
        return "list_flow"
    if view_type == "kanban":
        return "workspace_flow"
    if view_type == "search":
        return "entry_flow"
    if semantic_page.get("kanban_semantics"):
        return "workspace_flow"
    if semantic_page.get("list_semantics"):
        return "list_flow"
    if semantic_page.get("title_node"):
        return "detail_focus"
    return ""


def _semantic_interaction_mode(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    capability_flags = _as_dict(view_semantics.get("capability_flags"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))
    if view_type == "form":
        return "record_focus"
    if view_type in {"tree", "kanban"}:
        if capability_flags.get("is_editable") or capability_flags.get("can_create"):
            return "multi_select"
        if semantic_page.get("list_semantics") or semantic_page.get("kanban_semantics"):
            return "multi_select"
        return "browse"
    if view_type == "search":
        return "query"
    return ""


def resolve_scene_identity(
    *,
    scene_hint: Dict[str, Any] | None,
    page_hint: Dict[str, Any] | None,
    defaults: Dict[str, Any] | None = None,
    semantic_surface: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    fallback = defaults or {}
    scene_row = scene_hint or {}
    page_row = page_hint or {}
    parser_surface = semantic_surface if isinstance(semantic_surface, dict) else {}
    scene_key = _text(scene_row.get("key") or fallback.get("scene_key"))
    page_key = _text(page_row.get("key") or scene_row.get("page") or fallback.get("page_key"))
    page_route = _text(page_row.get("route") or fallback.get("page_route"))
    scene_type = _text(scene_row.get("scene_type") or fallback.get("scene_type"))
    layout_mode = _text(scene_row.get("layout_mode") or _semantic_layout_mode(parser_surface) or fallback.get("layout_mode"))
    page_goal = _text(scene_row.get("page_goal") or fallback.get("page_goal"))
    interaction_mode = _text(
        scene_row.get("interaction_mode") or _semantic_interaction_mode(parser_surface) or fallback.get("interaction_mode")
    )
    scene_version = _text(scene_row.get("scene_version") or fallback.get("scene_version"))

    parser_contract = _as_dict(parser_surface.get("parser_contract"))
    view_semantics = _as_dict(parser_surface.get("view_semantics"))
    model_name = _text(page_row.get("model") or fallback.get("model"))
    view_type = _text(page_row.get("view_type") or parser_contract.get("view_type") or view_semantics.get("source_view") or fallback.get("view_type"))
    title_field = _text(page_row.get("title_field") or fallback.get("title_field"))
    page_status = _text(page_row.get("page_status") or fallback.get("page_status"))
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
