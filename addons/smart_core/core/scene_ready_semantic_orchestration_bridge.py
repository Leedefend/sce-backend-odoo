# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _default_view_mode_label(mode: str) -> str:
    return {
        "tree": "列表",
        "kanban": "看板",
        "pivot": "透视",
        "graph": "图表",
        "calendar": "日历",
        "gantt": "甘特",
        "activity": "活动",
        "dashboard": "仪表板",
        "form": "表单",
        "search": "搜索",
    }.get(mode, mode)


def _semantic_view_candidates(surface: Dict[str, Any]) -> List[str]:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    native_view = _as_dict(surface.get("native_view"))
    candidates: List[str] = []
    for raw in (parser_contract.get("view_type"), view_semantics.get("source_view")):
        token = _text(raw)
        if token and token not in candidates:
            candidates.append(token)
    native_views = _as_dict(native_view.get("views"))
    for key in native_views.keys():
        token = _text(key)
        if token and token not in candidates:
            candidates.append(token)
    return candidates


def _selection_mode_from_semantics(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    capability_flags = _as_dict(view_semantics.get("capability_flags"))
    view_type = _text(parser_contract.get("view_type") or view_semantics.get("source_view"))

    if view_type == "form":
        return "single"
    if view_type in {"tree", "kanban"}:
        if capability_flags.get("is_editable") or capability_flags.get("can_create"):
            return "multi"
        if semantic_page.get("list_semantics") or semantic_page.get("kanban_semantics"):
            return "multi"
    return "single"


def apply_scene_ready_semantic_orchestration_bridge(
    payload: Dict[str, Any] | None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    parser_surface = _as_dict(out.get("parser_semantic_surface"))
    if not parser_surface:
        parser_surface = _as_dict(_as_dict(out.get("meta")).get("parser_semantic_surface"))
    if not parser_surface:
        return out

    candidates = _semantic_view_candidates(parser_surface)
    if candidates:
        out["view_modes"] = [
            {"key": mode, "label": _default_view_mode_label(mode), "enabled": True}
            for mode in candidates
        ]

    action_surface = _as_dict(out.get("action_surface"))
    if action_surface:
        action_surface["selection_mode"] = _selection_mode_from_semantics(parser_surface)
        out["action_surface"] = action_surface

    return out
