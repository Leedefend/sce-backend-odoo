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
    out["page"] = page

    render_hints = _as_dict(out.get("render_hints"))
    render_hints["semantic_profile"] = semantic_page_type
    render_hints["semantic_page_type"] = semantic_page_type
    out["render_hints"] = render_hints
    return out
