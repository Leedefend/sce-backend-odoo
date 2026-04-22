# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _resolve_semantic_layout(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))

    if view_type == "form":
        return "detail"
    if view_type == "tree":
        return "list"
    if view_type == "kanban":
        return "board"
    if view_type == "search":
        return "search"
    if semantic_page.get("list_semantics"):
        return "list"
    if semantic_page.get("kanban_semantics"):
        return "board"
    if semantic_page.get("title_node"):
        return "detail"
    return ""


def apply_scene_contract_semantic_orchestration_bridge(
    payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    governance = _as_dict(out.get("governance"))
    parser_surface = _as_dict(governance.get("parser_semantic_surface"))
    if not parser_surface:
        return out

    semantic_layout = _resolve_semantic_layout(parser_surface)
    if not semantic_layout:
        return out

    page = _as_dict(out.get("page"))
    page["layout"] = semantic_layout
    zones = []
    for zone in _as_list(page.get("zones")):
        if not isinstance(zone, dict):
            continue
        zone_copy = dict(zone)
        zone_copy["layout"] = semantic_layout
        zones.append(zone_copy)
    if zones:
        page["zones"] = zones
    out["page"] = page
    return out
