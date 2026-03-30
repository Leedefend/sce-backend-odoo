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


def _permission_allowed(value: Any, default: bool = False) -> bool:
    if isinstance(value, dict):
        if "allowed" in value:
            return bool(value.get("allowed"))
        if "visible" in value:
            return bool(value.get("visible"))
    if value in (None, ""):
        return default
    return bool(value)


def _fields_payload(out: Dict[str, Any]) -> Dict[str, Any]:
    meta = _as_dict(out.get("meta"))
    orchestrator = _as_dict(meta.get("ui_base_orchestrator_input"))
    field_fact = _as_dict(orchestrator.get("field_fact"))
    return _as_dict(field_fact.get("fields"))


def _permission_payload(out: Dict[str, Any]) -> Dict[str, Any]:
    permission_surface = _as_dict(out.get("permission_surface"))
    meta = _as_dict(out.get("meta"))
    orchestrator = _as_dict(meta.get("ui_base_orchestrator_input"))
    permission_fact = _as_dict(orchestrator.get("permission_fact"))
    payload: Dict[str, Any] = {}
    payload.update(permission_fact)
    if permission_surface:
        payload["surface"] = permission_surface
    return payload


def _has_active_field(out: Dict[str, Any]) -> bool:
    fields = _fields_payload(out)
    if "active" in fields:
        return True
    list_surface = _as_dict(out.get("list_surface"))
    for row in _as_list(list_surface.get("columns")) + _as_list(list_surface.get("hidden_columns")):
        payload = _as_dict(row)
        if _text(payload.get("field") or payload.get("name") or row) == "active":
            return True
    return False


def _native_can_delete(out: Dict[str, Any], surface: Dict[str, Any]) -> bool:
    view_semantics = _as_dict(surface.get("view_semantics"))
    capability_flags = _as_dict(view_semantics.get("capability_flags"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    editable = _as_dict(list_semantics.get("editable"))
    permission_payload = _permission_payload(out)
    unlink_allowed = _permission_allowed(permission_payload.get("unlink"), default=True)
    return bool(
        capability_flags.get("can_delete", True)
        and editable.get("can_delete", True)
        and unlink_allowed
    )


def _native_can_write(out: Dict[str, Any]) -> bool:
    permission_payload = _permission_payload(out)
    if isinstance(permission_payload.get("surface"), dict) and "allowed" in _as_dict(permission_payload.get("surface")):
        return _permission_allowed(_as_dict(permission_payload.get("surface")).get("allowed"), default=True)
    return _permission_allowed(permission_payload.get("write"), default=True)


def _derive_batch_capabilities(out: Dict[str, Any], surface: Dict[str, Any], selection_mode: str) -> Dict[str, Any]:
    view_type = _view_type(surface)
    has_active_field = _has_active_field(out)
    can_write = _native_can_write(out)
    can_delete = _native_can_delete(out, surface)
    selection_required = selection_mode == "multi"
    can_toggle_active = bool(selection_required and has_active_field and can_write)
    return {
        "can_delete": bool(selection_required and can_delete),
        "can_archive": can_toggle_active,
        "can_activate": can_toggle_active,
        "selection_required": selection_required,
        "native_basis": {
            "view_type": view_type,
            "selection_mode": selection_mode,
            "has_active_field": has_active_field,
            "permission_write": can_write,
            "permission_unlink": _permission_allowed(_permission_payload(out).get("unlink"), default=True),
            "tree_can_delete": can_delete,
        },
    }


def apply_scene_ready_action_semantic_bridge(payload: Dict[str, Any] | None) -> Dict[str, Any]:
    out = dict(payload or {})
    parser_surface = _as_dict(out.get("parser_semantic_surface"))
    if not parser_surface:
        parser_surface = _as_dict(_as_dict(out.get("meta")).get("parser_semantic_surface"))
    action_surface = _as_dict(out.get("action_surface"))
    actions = [row for row in _as_list(out.get("actions")) if isinstance(row, dict)]
    if not parser_surface:
        return out

    view_type = _view_type(parser_surface)
    shape = _group_shape(view_type)
    selection_mode = _text(action_surface.get("selection_mode")) or "single"
    action_surface["batch_capabilities"] = _derive_batch_capabilities(out, parser_surface, selection_mode)
    action_keys = [_text(row.get("key")) for row in actions if _text(row.get("key"))]
    if action_keys:
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
