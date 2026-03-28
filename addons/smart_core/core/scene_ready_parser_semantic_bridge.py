# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


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


def apply_scene_ready_parser_semantic_bridge(
    compiled: Dict[str, Any] | None,
    normalized_contract: Dict[str, Any] | None,
) -> Dict[str, Any]:
    payload = dict(compiled or {})
    contract = dict(normalized_contract or {})

    parser_contract = _as_dict(contract.get("parser_contract"))
    view_semantics = _as_dict(contract.get("view_semantics"))
    native_view = _as_dict(contract.get("native_view"))

    if not (parser_contract or view_semantics or native_view):
        return payload

    meta = _as_dict(payload.get("meta"))
    meta["parser_semantic_surface"] = {
        "parser_contract": parser_contract,
        "view_semantics": view_semantics,
        "native_view": native_view,
    }
    payload["meta"] = meta

    if not _as_list(payload.get("view_modes")):
        requested = _text(parser_contract.get("view_type"))
        native_views = _as_dict(native_view.get("views"))
        candidates: List[str] = []
        for item in (requested, _text(view_semantics.get("source_view"))):
            if item and item not in candidates:
                candidates.append(item)
        for key in native_views.keys():
            token = _text(key)
            if token and token not in candidates:
                candidates.append(token)
        if candidates:
            payload["view_modes"] = [{"key": mode, "label": _default_view_mode_label(mode), "enabled": True} for mode in candidates]

    surface = _as_dict(payload.get("surface"))
    if view_semantics and not _as_dict(surface.get("semantic_view")):
        surface["semantic_view"] = {
            "source_view": _text(view_semantics.get("source_view")),
            "capability_flags": _as_dict(view_semantics.get("capability_flags")),
            "semantic_meta": _as_dict(view_semantics.get("semantic_meta")),
        }
    if surface:
        payload["surface"] = surface

    return payload
