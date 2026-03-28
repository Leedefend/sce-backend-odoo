# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _view_type(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    return _text(parser_contract.get("view_type") or view_semantics.get("source_view"))


def _group_shape(view_type: str) -> Dict[str, str]:
    return {
        "form": {"key": "record_actions", "label": "记录操作"},
        "tree": {"key": "list_actions", "label": "列表操作"},
        "kanban": {"key": "card_actions", "label": "卡片操作"},
        "search": {"key": "search_actions", "label": "搜索操作"},
    }.get(view_type, {"key": "workflow", "label": "流程推进"})


def _primary_limit(view_type: str) -> int:
    if view_type == "form":
        return 2
    if view_type in {"tree", "kanban"}:
        return 3
    return 3


def apply_scene_ready_action_semantic_bridge(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    out = dict(payload or {})
    parser_surface = _as_dict(out.get("parser_semantic_surface"))
    if not parser_surface:
        parser_surface = _as_dict(_as_dict(out.get("meta")).get("parser_semantic_surface"))
    action_surface = _as_dict(out.get("action_surface"))
    actions = [row for row in _as_list(out.get("actions")) if isinstance(row, dict)]
    if not (parser_surface and actions):
        return out

    view_type = _view_type(parser_surface)
    shape = _group_shape(view_type)
    action_keys = [_text(row.get("key")) for row in actions if _text(row.get("key"))]
    if not action_keys:
        return out

    action_surface["primary_actions"] = action_keys[: _primary_limit(view_type)]
    action_surface["groups"] = [
        {
            "key": shape["key"],
            "label": shape["label"],
            "actions": action_keys,
        }
    ]
    out["action_surface"] = action_surface
    return out
