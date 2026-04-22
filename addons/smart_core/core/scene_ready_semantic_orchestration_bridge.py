# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _handoff_consume_mode(family: str) -> str:
    token = _text(family)
    if token in {"payment_approval", "payment_entry"}:
        return "advisory"
    return "direct"


def _build_runtime_handoff_surface(payload: Dict[str, Any]) -> Dict[str, Any]:
    handoff = _as_dict(payload.get("delivery_handoff_v1"))
    if not handoff:
        return {}

    family = _text(handoff.get("family"))
    primary_action = _as_dict(handoff.get("primary_action"))
    acceptance = _as_dict(handoff.get("acceptance"))
    return {
        "family": family,
        "consume_mode": _handoff_consume_mode(family),
        "runtime_entry_type": _text(handoff.get("runtime_entry_type")) or "governed_user_flow",
        "runtime_consumer": _text(handoff.get("runtime_consumer")) or "family_runtime_consumer",
        "runtime_mode": _text(handoff.get("runtime_mode")) or "direct",
        "user_entry": _text(handoff.get("user_entry")),
        "final_scene": _text(handoff.get("final_scene")),
        "primary_action": primary_action,
        "required_provider": _text(handoff.get("required_provider")),
        "fallback_policy": _as_dict(handoff.get("fallback_policy")),
        "workflow_ready": bool(acceptance.get("workflow_ready")),
        "runtime_ready": bool(acceptance.get("runtime_ready")),
        "advisory_only": bool(acceptance.get("advisory_only")),
    }


def _build_product_delivery_surface(runtime_handoff_surface: Dict[str, Any]) -> Dict[str, Any]:
    runtime_handoff = _as_dict(runtime_handoff_surface)
    if not runtime_handoff:
        return {}

    consume_mode = _text(runtime_handoff.get("consume_mode")) or "direct"
    direct_delivery = consume_mode == "direct"
    primary_action = _as_dict(runtime_handoff.get("primary_action"))

    return {
        "family": _text(runtime_handoff.get("family")),
        "delivery_mode": "direct_delivery" if direct_delivery else "advisory_only",
        "entry_kind": "primary_action" if primary_action else "guidance_only",
        "entry_action": primary_action,
        "final_scene": _text(runtime_handoff.get("final_scene")),
        "user_entry": _text(runtime_handoff.get("user_entry")),
        "required_provider": _text(runtime_handoff.get("required_provider")),
        "fallback_policy": _as_dict(runtime_handoff.get("fallback_policy")),
        "advisory": {
            "enabled": not direct_delivery,
            "reason": "family_remains_advisory_in_wave_1" if not direct_delivery else "",
        },
        "acceptance": {
            "runtime_ready": bool(runtime_handoff.get("runtime_ready")),
            "workflow_ready": bool(runtime_handoff.get("workflow_ready")),
            "advisory_only": not direct_delivery,
        },
    }


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


def _build_switch_surface(
    scene_key: str,
    related_scenes: List[Any],
    scene_catalog: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    keys: List[str] = []
    current_key = _text(scene_key)
    if current_key:
        keys.append(current_key)
    for raw in related_scenes:
        key = _text(raw)
        if key and key not in keys:
            keys.append(key)

    items: List[Dict[str, Any]] = []
    for key in keys:
        catalog_row = _as_dict(scene_catalog.get(key))
        route = _text(catalog_row.get("route")) or f"/s/{key}"
        label = _text(catalog_row.get("label")) or key
        items.append(
            {
                "key": key,
                "label": label,
                "route": route,
                "active": key == current_key,
                "enabled": key != current_key,
            }
        )
    if len(items) <= 1:
        return {}
    return {
        "current_scene_key": current_key,
        "items": items,
    }


def apply_scene_ready_semantic_orchestration_bridge(
    payload: Dict[str, Any] | None,
    *,
    scene_key: str = "",
    scene_catalog: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    out = dict(payload or {})
    parser_surface = _as_dict(out.get("parser_semantic_surface"))
    if not parser_surface:
        parser_surface = _as_dict(_as_dict(out.get("meta")).get("parser_semantic_surface"))
    if parser_surface:
        candidates = _semantic_view_candidates(parser_surface)
        if candidates:
            out["view_modes"] = [
                {"key": mode, "label": _default_view_mode_label(mode), "enabled": True}
                for mode in candidates
            ]

        action_surface = _as_dict(out.get("action_surface"))
        action_surface["selection_mode"] = _selection_mode_from_semantics(parser_surface)
        out["action_surface"] = action_surface

    switch_surface = _build_switch_surface(
        _text(scene_key) or _text(_as_dict(out.get("scene")).get("key")),
        _as_list(out.pop("related_scenes", [])),
        _as_dict(scene_catalog),
    )
    if switch_surface:
        out["switch_surface"] = switch_surface

    runtime_handoff_surface = _build_runtime_handoff_surface(out)
    if runtime_handoff_surface:
        out["runtime_handoff_surface"] = runtime_handoff_surface
        product_delivery_surface = _build_product_delivery_surface(runtime_handoff_surface)
        if product_delivery_surface:
            out["product_delivery_surface"] = product_delivery_surface

    return out
