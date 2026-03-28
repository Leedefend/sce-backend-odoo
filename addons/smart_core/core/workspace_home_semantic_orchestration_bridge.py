# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _semantic_page_type(surface: Dict[str, Any]) -> str:
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


def _search_actions(surface: Dict[str, Any]) -> list[Dict[str, Any]]:
    native_view = _as_dict(surface.get("native_view"))
    search_view = _as_dict(_as_dict(native_view.get("views")).get("search"))
    if not (
        _as_list(search_view.get("filters"))
        or _as_list(search_view.get("group_bys"))
        or _as_list(search_view.get("searchpanel"))
    ):
        return []
    return [
        {"key": "apply_filters", "label": "应用筛选", "intent": "ui.contract"},
        {"key": "reset_filters", "label": "重置筛选", "intent": "ui.contract"},
    ]


def apply_workspace_home_semantic_orchestration_bridge(
    payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    orchestration = _as_dict(out.get("page_orchestration_v1"))
    meta = _as_dict(orchestration.get("meta"))
    surface = _as_dict(meta.get("parser_semantic_surface"))
    if not surface:
        return out

    semantic_page_type = _semantic_page_type(surface)
    page = _as_dict(orchestration.get("page"))
    render_hints = _as_dict(orchestration.get("render_hints"))

    if semantic_page_type == "workspace":
        page["layout_mode"] = "workspace_flow"
        render_hints["preferred_columns"] = 2
    elif semantic_page_type == "detail":
        page["layout_mode"] = "detail_focus"
        render_hints["preferred_columns"] = 1
    elif semantic_page_type == "list":
        page["layout_mode"] = "list_flow"
        render_hints["preferred_columns"] = 2
    elif semantic_page_type == "entry_hub":
        page["layout_mode"] = "entry_flow"
        render_hints["preferred_columns"] = 1

    semantic_actions = _search_actions(surface)
    if semantic_actions:
        existing = [row for row in _as_list(page.get("global_actions")) if isinstance(row, dict)]
        existing_keys = {_text(row.get("key")) for row in existing}
        merged = list(semantic_actions)
        for row in existing:
            key = _text(row.get("key"))
            if key in {"apply_filters", "reset_filters"} and key in existing_keys:
                continue
            merged.append(row)
        page["global_actions"] = merged

    if semantic_page_type:
        render_hints["semantic_page_type"] = semantic_page_type
    orchestration["page"] = page
    orchestration["render_hints"] = render_hints
    out["page_orchestration_v1"] = orchestration
    return out
