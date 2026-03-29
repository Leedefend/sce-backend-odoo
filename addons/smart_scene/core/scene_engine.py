# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List

from .layout_orchestrator import apply_zone_priority
from .scene_contract_builder import build_scene_contract
from .scene_resolver import resolve_scene_identity
from .structure_mapper import map_zone_specs_to_blocks


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) == 0
    return False


def _workflow_surface_nonempty(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    return bool(_text(payload.get("state_field")) or _as_list(payload.get("states")) or _as_list(payload.get("transitions")))


def _validation_surface_nonempty(surface: Dict[str, Any]) -> bool:
    payload = _as_dict(surface)
    return bool(_as_list(payload.get("required_fields")) or _as_list(payload.get("field_rules")))


def _derive_record_state_summary(
    workflow_surface: Dict[str, Any],
    validation_surface: Dict[str, Any],
    record: Dict[str, Any],
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    if _workflow_surface_nonempty(workflow_surface):
        state_field = _text(workflow_surface.get("state_field"))
        current_state = _text(record.get(state_field)) if state_field else ""
        transitions = _as_list(workflow_surface.get("transitions"))
        active_transitions = [
            row
            for row in transitions
            if isinstance(row, dict) and (not _text(row.get("from")) or _text(row.get("from")) == current_state)
        ]
        summary.update(
            {
                "state_field": state_field,
                "current_state": current_state,
                "states": _as_list(workflow_surface.get("states")),
                "transitions": transitions,
                "active_transitions": active_transitions,
                "active_transition_targets": [
                    _text(row.get("to")) for row in active_transitions if _text(row.get("to"))
                ],
                "highlight_states": _as_list(workflow_surface.get("highlight_states")),
                "workflow_transition_count": len(transitions),
                "active_transition_count": len(active_transitions),
            }
        )
    if _validation_surface_nonempty(validation_surface):
        required_fields = _as_list(validation_surface.get("required_fields"))
        missing_required_fields = [
            field for field in required_fields if _text(field) and _empty_value(record.get(_text(field)))
        ]
        summary.update(
            {
                "validation_required_fields": required_fields,
                "validation_required_count": len(required_fields),
                "validation_rule_count": len(_as_list(validation_surface.get("field_rules"))),
                "missing_required_fields": missing_required_fields,
                "missing_required_count": len(missing_required_fields),
            }
        )
    return summary


def _derive_permissions_from_semantic_surface(surface: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = _as_dict(surface)
    permission_surface = _as_dict(payload.get("permission_surface"))
    workflow_surface = _as_dict(payload.get("workflow_surface"))
    validation_surface = _as_dict(payload.get("validation_surface"))
    if not permission_surface and not _workflow_surface_nonempty(workflow_surface) and not _validation_surface_nonempty(validation_surface):
        return {}

    visible = bool(permission_surface.get("visible", True))
    allowed = bool(permission_surface.get("allowed", True))
    reason_code = _text(permission_surface.get("reason_code"))
    record = _as_dict(payload.get("record"))
    state_field = _text(workflow_surface.get("state_field"))
    current_state = _text(record.get(state_field)) if state_field else ""
    transitions = _as_list(workflow_surface.get("transitions"))
    active_transitions = [
        row
        for row in transitions
        if isinstance(row, dict) and (not _text(row.get("from")) or _text(row.get("from")) == current_state)
    ]
    missing_required_fields = [
        field
        for field in _as_list(validation_surface.get("required_fields"))
        if _text(field) and _empty_value(record.get(_text(field)))
    ]
    disabled_actions: Dict[str, Any] = {}
    if visible and not allowed:
        disabled_actions["edit"] = reason_code or "readonly"
        disabled_actions["create"] = reason_code or "readonly"
        disabled_actions["delete"] = reason_code or "readonly"
        if _workflow_surface_nonempty(workflow_surface):
            disabled_actions["workflow"] = "permission_workflow_gate"
    if visible and allowed and missing_required_fields:
        disabled_actions["submit"] = "validation_required"

    record_state_summary = _derive_record_state_summary(workflow_surface, validation_surface, record)
    if _workflow_surface_nonempty(workflow_surface):
        if visible and allowed and not active_transitions:
            disabled_actions["workflow"] = "action_permission_workflow_gate"
    return {
        "can_read": visible,
        "can_edit": allowed,
        "disabled_actions": disabled_actions,
        "record_state_summary": record_state_summary,
    }


def build_scene_contract_from_specs(
    *,
    scene_hint: Dict[str, Any],
    page_hint: Dict[str, Any],
    zone_specs: List[Dict[str, Any]],
    built_zones: Dict[str, Any],
    zone_order: List[str] | None = None,
    record: Dict[str, Any] | None = None,
    diagnostics: Dict[str, Any] | None = None,
    nav_ref: Dict[str, Any] | None = None,
    semantic_surface: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    semantic_payload = dict(semantic_surface or {})
    semantic_payload["record"] = dict(record or {})
    resolved = resolve_scene_identity(scene_hint=scene_hint, page_hint=page_hint, semantic_surface=semantic_payload)
    mapped_specs = map_zone_specs_to_blocks(zone_specs)
    ordered_specs = apply_zone_priority(mapped_specs, zone_order=zone_order)
    diagnostics_payload = dict(diagnostics or {})
    diagnostics_payload.setdefault("scene_engine", "smart_scene.core.scene_engine")
    diagnostics_payload.setdefault("zone_specs_mapped", ordered_specs)
    derived_permissions = _derive_permissions_from_semantic_surface(semantic_payload)
    return build_scene_contract(
        scene=resolved.get("scene") or {},
        page=resolved.get("page") or {},
        zones=built_zones,
        record=record or {},
        nav_ref=nav_ref or {
            "active_scene_key": str((resolved.get("scene") or {}).get("scene_key") or "").strip(),
            "active_menu_id": page_hint.get("menu_id") if isinstance(page_hint, dict) else None,
        },
        permissions=derived_permissions,
        diagnostics=diagnostics_payload,
        semantic_surface=semantic_payload,
    )
