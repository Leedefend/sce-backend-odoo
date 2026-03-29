# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _permission_surface_restricted(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    if not payload:
        return False
    if "visible" in payload and not bool(payload.get("visible", True)):
        return True
    if "allowed" in payload and not bool(payload.get("allowed", True)):
        return True
    return False


def _permission_surface_page_status(surface: Dict[str, Any]) -> str:
    payload = _as_dict(surface)
    if not payload:
        return ""
    if "visible" in payload and not bool(payload.get("visible", True)):
        return "restricted"
    if "allowed" in payload and not bool(payload.get("allowed", True)):
        return "readonly"
    return ""


def _search_surface_nonempty(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    return bool(
        _text(payload.get("default_sort"))
        or _text(payload.get("mode"))
        or payload.get("filters")
        or payload.get("fields")
        or payload.get("group_by")
        or payload.get("searchpanel")
    )


def _workflow_surface_nonempty(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    return bool(_text(payload.get("state_field")) or payload.get("states") or payload.get("transitions"))


def _validation_surface_nonempty(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    return bool(payload.get("required_fields") or payload.get("field_rules"))


def _empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def _semantic_page_closed_state(surface: Dict[str, Any]) -> tuple[bool, str]:
    semantic_page = _as_dict(surface.get("semantic_page"))
    action_gating = _as_dict(semantic_page.get("action_gating"))
    record = _as_dict(surface.get("record"))
    record_state = _as_dict(action_gating.get("record_state"))
    policy = _as_dict(action_gating.get("policy"))
    verdict = _as_dict(action_gating.get("verdict"))
    closed_states = {_text(value) for value in _as_list(policy.get("closed_states")) if _text(value)}
    state_field = _text(record_state.get("field"))
    current_state = _text(record.get(state_field)) if state_field else _text(record_state.get("value"))
    if verdict.get("is_closed_state") is True:
        return True, _text(verdict.get("reason_code"))
    if current_state and current_state in closed_states:
        return True, _text(verdict.get("reason_code"))
    return False, _text(verdict.get("reason_code"))


def _semantic_page_status(surface: Dict[str, Any], fallback_status: str = "") -> str:
    permission_surface = _as_dict(surface.get("permission_surface"))
    status = _permission_surface_page_status(permission_surface)
    if status:
        return status
    is_closed_state, _ = _semantic_page_closed_state(surface)
    if is_closed_state:
        return "readonly"

    record = _as_dict(surface.get("record"))
    workflow_surface = _as_dict(surface.get("workflow_surface"))
    validation_surface = _as_dict(surface.get("validation_surface"))
    required_fields = [field for field in _as_list(validation_surface.get("required_fields")) if _text(field)]
    missing_required_fields = [field for field in required_fields if _empty_value(record.get(field))]
    transitions = _as_list(workflow_surface.get("transitions"))
    state_field = _text(workflow_surface.get("state_field"))
    current_state = _text(record.get(state_field)) if state_field else ""
    active_transitions = [
        row
        for row in transitions
        if isinstance(row, dict) and (not _text(row.get("from")) or _text(row.get("from")) == current_state)
    ]

    if missing_required_fields and not record:
        return "empty"
    if (_workflow_surface_nonempty(workflow_surface) or _validation_surface_nonempty(validation_surface)) and not missing_required_fields:
        if active_transitions or required_fields or _as_list(workflow_surface.get("states")):
            return "ready"
    return fallback_status


def _semantic_layout_mode(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    search_surface = _as_dict(surface.get("search_surface"))
    workflow_surface = _as_dict(surface.get("workflow_surface"))
    validation_surface = _as_dict(surface.get("validation_surface"))
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
    if _search_surface_nonempty(search_surface):
        return "entry_flow"
    if _workflow_surface_nonempty(workflow_surface) or _validation_surface_nonempty(validation_surface):
        return "detail_focus"
    if semantic_page.get("title_node"):
        return "detail_focus"
    return ""


def _semantic_interaction_mode(surface: Dict[str, Any]) -> str:
    parser_contract = _as_dict(surface.get("parser_contract"))
    view_semantics = _as_dict(surface.get("view_semantics"))
    semantic_page = _as_dict(surface.get("semantic_page"))
    search_surface = _as_dict(surface.get("search_surface"))
    workflow_surface = _as_dict(surface.get("workflow_surface"))
    validation_surface = _as_dict(surface.get("validation_surface"))
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
    if _search_surface_nonempty(search_surface):
        return "query"
    if _workflow_surface_nonempty(workflow_surface) or _validation_surface_nonempty(validation_surface):
        return "record_focus"
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
    semantic_page = _as_dict(parser_surface.get("semantic_page"))
    view_semantics = _as_dict(parser_surface.get("view_semantics"))
    search_surface = _as_dict(parser_surface.get("search_surface"))
    workflow_surface = _as_dict(parser_surface.get("workflow_surface"))
    validation_surface = _as_dict(parser_surface.get("validation_surface"))
    permission_surface = _as_dict(parser_surface.get("permission_surface"))
    record_surface = _as_dict(parser_surface.get("record"))
    model_name = _text(page_row.get("model") or fallback.get("model"))
    view_type = _text(
        page_row.get("view_type")
        or parser_contract.get("view_type")
        or view_semantics.get("source_view")
        or ("search" if _search_surface_nonempty(search_surface) else "")
        or ("form" if (_workflow_surface_nonempty(workflow_surface) or _validation_surface_nonempty(validation_surface)) else "")
        or fallback.get("view_type")
    )
    title_field = _text(page_row.get("title_field") or fallback.get("title_field"))
    page_status = _text(
        page_row.get("page_status")
        or _semantic_page_status(
            {
                "permission_surface": permission_surface,
                "semantic_page": semantic_page,
                "workflow_surface": workflow_surface,
                "validation_surface": validation_surface,
                "record": record_surface,
            },
            _text(fallback.get("page_status")),
        )
    )
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
