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
    semantic_page: Dict[str, Any],
    runtime_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    state = _as_dict(runtime_state)
    if _workflow_surface_nonempty(workflow_surface):
        summary.update(
            {
                "state_field": _text(state.get("state_field") or workflow_surface.get("state_field")),
                "current_state": _text(state.get("current_state")),
                "states": _as_list(state.get("states") or workflow_surface.get("states")),
                "transitions": _as_list(state.get("transitions") or workflow_surface.get("transitions")),
                "active_transitions": _as_list(state.get("active_transitions")),
                "active_transition_targets": [
                    _text(row.get("to")) for row in _as_list(state.get("active_transitions")) if _text(row.get("to"))
                ],
                "highlight_states": _as_list(state.get("highlight_states") or workflow_surface.get("highlight_states")),
                "workflow_transition_count": int(state.get("workflow_transition_count") or 0),
                "active_transition_count": int(state.get("active_transition_count") or 0),
            }
        )
    if _validation_surface_nonempty(validation_surface):
        summary.update(
            {
                "validation_required_fields": _as_list(state.get("validation_required_fields") or validation_surface.get("required_fields")),
                "validation_required_count": int(state.get("validation_required_count") or 0),
                "validation_rule_count": int(state.get("validation_rule_count") or 0),
                "missing_required_fields": _as_list(state.get("missing_required_fields")),
                "missing_required_count": int(state.get("missing_required_count") or 0),
            }
        )
    if _as_list(state.get("closed_states")) or _text(state.get("closed_state_reason_code")):
        summary.update(
            {
                "closed_states": _as_list(state.get("closed_states")),
                "is_closed_state": bool(state.get("is_closed_state")),
                "closed_state_reason_code": _text(state.get("closed_state_reason_code")),
                "page_status": _text(state.get("page_status")),
            }
        )
    return summary


def _derive_lifecycle_display(summary: Dict[str, Any]) -> Dict[str, Any]:
    payload = _as_dict(summary)
    if not _text(payload.get("state_field")) and not _as_list(payload.get("states")):
        return {}
    current_state = _text(payload.get("current_state"))
    highlight_states = {_text(value) for value in _as_list(payload.get("highlight_states")) if _text(value)}
    steps: List[Dict[str, Any]] = []
    for row in _as_list(payload.get("states")):
        if isinstance(row, dict):
            key = _text(row.get("key") or row.get("value") or row.get("name"))
            label = _text(row.get("label") or row.get("string") or key)
        else:
            key = _text(row)
            label = key
        if not key:
            continue
        steps.append(
            {
                "key": key,
                "label": label,
                "active": bool(current_state and key == current_state),
                "highlight": key in highlight_states,
            }
        )
    return {
        "owner_layer": "scene_orchestration",
        "source": "permissions.record_state_summary",
        "state_field": _text(payload.get("state_field")),
        "current_state": current_state,
        "steps": steps,
        "allowed_transitions": _as_list(payload.get("active_transitions")),
        "transition_count": int(payload.get("workflow_transition_count") or 0),
        "active_transition_count": int(payload.get("active_transition_count") or 0),
        "page_status": _text(payload.get("page_status")),
    }


def _derive_list_search_profile(semantic_payload: Dict[str, Any]) -> Dict[str, Any]:
    semantic_page = _as_dict(semantic_payload.get("semantic_page"))
    list_semantics = _as_dict(semantic_page.get("list_semantics"))
    search_surface = _as_dict(semantic_payload.get("search_surface"))
    columns = _as_list(list_semantics.get("columns"))
    if not columns and not search_surface:
        return {}
    filters = _as_list(search_surface.get("filters") or search_surface.get("searchpanel"))
    return {
        "owner_layer": "scene_orchestration",
        "source": "semantic_page.list_semantics",
        "columns": columns,
        "row_primary": _text(list_semantics.get("row_primary")),
        "row_secondary": _text(list_semantics.get("row_secondary")),
        "status_field": _text(list_semantics.get("status_field")),
        "search_mode": _text(search_surface.get("mode")),
        "filters": filters,
        "filter_count": len(filters),
    }


def _derive_relation_entries(semantic_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    semantic_page = _as_dict(semantic_payload.get("semantic_page"))
    entries: List[Dict[str, Any]] = []
    for row in _as_list(semantic_page.get("relation_entries")):
        item = _as_dict(row)
        field = _text(item.get("field"))
        model = _text(item.get("model"))
        if not field or not model:
            continue
        entries.append(
            {
                "field": field,
                "model": model,
                "create_mode": _text(item.get("create_mode") or "disabled"),
                "can_read": bool(item.get("can_read", True)),
                "can_create": bool(item.get("can_create", False)),
                "reason_code": _text(item.get("reason_code")),
                "default_vals": _as_dict(item.get("default_vals")),
                "action_id": item.get("action_id"),
                "menu_id": item.get("menu_id"),
                "owner_layer": "scene_orchestration",
                "source": _text(item.get("source") or "semantic_page.relation_entries"),
            }
        )
    return entries


def _build_scene_envelope_presence(
    *,
    semantic_payload: Dict[str, Any],
    page_payload: Dict[str, Any],
    derived_actions: Dict[str, Any],
) -> Dict[str, Any]:
    semantic_page = _as_dict(semantic_payload.get("semantic_page"))
    scene_presence = {
        "action_surface": bool(
            _as_list(derived_actions.get("primary_actions"))
            or _as_list(derived_actions.get("secondary_actions"))
            or _as_list(derived_actions.get("contextual_actions"))
            or _as_list(derived_actions.get("danger_actions"))
            or _as_list(derived_actions.get("recommended_actions"))
        ),
        "lifecycle": bool(_as_dict(page_payload.get("lifecycle"))),
        "list_profile": bool(_as_dict(page_payload.get("list_profile"))),
        "relation_entries": bool(_as_list(page_payload.get("relation_entries"))),
    }
    compatibility_presence = {
        "action_groups": bool(_as_list(semantic_page.get("action_groups"))),
        "lifecycle": bool(_as_dict(semantic_page.get("lifecycle")) or _as_dict(semantic_payload.get("lifecycle"))),
        "list_profile": bool(_as_dict(semantic_page.get("list_profile")) or _as_dict(semantic_payload.get("list_profile"))),
        "field_relation_entry": bool(_as_list(semantic_page.get("relation_entries"))),
    }
    return {
        "scene_envelope_presence": scene_presence,
        "compatibility_field_presence": compatibility_presence,
    }


def _semantic_page_closed_state(semantic_page: Dict[str, Any], record: Dict[str, Any]) -> tuple[bool, str]:
    action_gating = _as_dict(semantic_page.get("action_gating"))
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


def _derive_semantic_runtime_state(
    *,
    permission_surface: Dict[str, Any],
    workflow_surface: Dict[str, Any],
    validation_surface: Dict[str, Any],
    semantic_page: Dict[str, Any],
    record: Dict[str, Any],
) -> Dict[str, Any]:
    visible = bool(permission_surface.get("visible", True))
    allowed = bool(permission_surface.get("allowed", True))
    state_field = _text(workflow_surface.get("state_field"))
    current_state = _text(record.get(state_field)) if state_field else ""
    transitions = _as_list(workflow_surface.get("transitions"))
    active_transitions = [
        row
        for row in transitions
        if isinstance(row, dict) and (not _text(row.get("from")) or _text(row.get("from")) == current_state)
    ]
    required_fields = [field for field in _as_list(validation_surface.get("required_fields")) if _text(field)]
    missing_required_fields = [field for field in required_fields if _empty_value(record.get(_text(field)))]
    is_closed_state, closed_reason = _semantic_page_closed_state(semantic_page, record)

    page_status = ""
    if not visible:
        page_status = "restricted"
    elif not allowed or is_closed_state:
        page_status = "readonly"
    elif missing_required_fields and not record:
        page_status = "empty"
    elif (_workflow_surface_nonempty(workflow_surface) or _validation_surface_nonempty(validation_surface)) and not missing_required_fields:
        if active_transitions or required_fields or _as_list(workflow_surface.get("states")):
            page_status = "ready"

    return {
        "state_field": state_field,
        "current_state": current_state,
        "states": _as_list(workflow_surface.get("states")),
        "transitions": transitions,
        "active_transitions": active_transitions,
        "highlight_states": _as_list(workflow_surface.get("highlight_states")),
        "workflow_transition_count": len(transitions),
        "active_transition_count": len(active_transitions),
        "validation_required_fields": required_fields,
        "validation_required_count": len(required_fields),
        "validation_rule_count": len(_as_list(validation_surface.get("field_rules"))),
        "missing_required_fields": missing_required_fields,
        "missing_required_count": len(missing_required_fields),
        "closed_states": [state for state in _as_list(_as_dict(_as_dict(semantic_page.get("action_gating")).get("policy")).get("closed_states")) if _text(state)],
        "is_closed_state": is_closed_state,
        "closed_state_reason_code": closed_reason,
        "page_status": page_status,
    }


def _apply_permission_verdicts(
    *,
    semantic_page: Dict[str, Any],
    allowed: bool,
    visible: bool,
    disabled_actions: Dict[str, Any],
) -> Dict[str, Any]:
    verdicts = _as_dict(semantic_page.get("permission_verdicts"))
    read_verdict = _as_dict(verdicts.get("read"))
    create_verdict = _as_dict(verdicts.get("create"))
    write_verdict = _as_dict(verdicts.get("write"))
    unlink_verdict = _as_dict(verdicts.get("unlink"))
    execute_verdict = _as_dict(verdicts.get("execute"))

    can_read = visible and bool(read_verdict.get("allowed", True))
    can_edit = allowed and bool(write_verdict.get("allowed", allowed))
    can_create = allowed and bool(create_verdict.get("allowed", False))
    can_delete = allowed and bool(unlink_verdict.get("allowed", False))

    if not can_create and _text(create_verdict.get("reason_code")):
        disabled_actions.setdefault("create", _text(create_verdict.get("reason_code")))
    if not can_edit and _text(write_verdict.get("reason_code")):
        disabled_actions.setdefault("edit", _text(write_verdict.get("reason_code")))
    if not can_delete and _text(unlink_verdict.get("reason_code")):
        disabled_actions.setdefault("delete", _text(unlink_verdict.get("reason_code")))
    if not bool(execute_verdict.get("allowed", True)) and _text(execute_verdict.get("reason_code")):
        disabled_actions.setdefault("execute", _text(execute_verdict.get("reason_code")))

    return {
        "can_read": can_read,
        "can_edit": can_edit,
        "can_create": can_create,
        "can_delete": can_delete,
    }


def _apply_action_semantics(
    *,
    semantic_page: Dict[str, Any],
    disabled_actions: Dict[str, Any],
) -> None:
    actions = _as_dict(semantic_page.get("actions"))
    for group_key in ("header_actions", "record_actions", "toolbar_actions"):
        for row in _as_list(actions.get(group_key)):
            item = _as_dict(row)
            action_key = _text(item.get("key"))
            if not action_key:
                continue
            reason_code = _infer_action_reason(item=item, disabled_actions=disabled_actions)
            if reason_code:
                disabled_actions.setdefault(action_key, reason_code)


def _infer_action_operation(action_key: str) -> str:
    lowered = _text(action_key).lower()
    if any(token in lowered for token in ("create", "new", "add")):
        return "create"
    if any(token in lowered for token in ("delete", "unlink", "remove")):
        return "delete"
    if any(token in lowered for token in ("workflow", "approve", "reject", "transition")):
        return "workflow"
    if any(token in lowered for token in ("submit", "confirm")):
        return "submit"
    if any(token in lowered for token in ("edit", "write", "archive", "save")):
        return "edit"
    return ""


def _infer_action_reason(
    *,
    item: Dict[str, Any],
    disabled_actions: Dict[str, Any],
) -> str:
    action_key = _text(item.get("key"))
    if not action_key:
        return ""
    if _text(disabled_actions.get(action_key)):
        return _text(disabled_actions.get(action_key))

    enabled = bool(item.get("enabled", True))
    reason_code = _text(item.get("reason_code"))
    if not enabled and reason_code:
        return reason_code

    gate = _as_dict(item.get("gate"))
    if gate and not bool(gate.get("allowed", True)) and _text(gate.get("reason_code")):
        return _text(gate.get("reason_code"))

    inferred_operation = _infer_action_operation(action_key)
    if inferred_operation and _text(disabled_actions.get(inferred_operation)):
        return _text(disabled_actions.get(inferred_operation))
    if bool(gate.get("requires_write")) and _text(disabled_actions.get("edit")):
        return _text(disabled_actions.get("edit"))
    if _text(disabled_actions.get("execute")):
        return _text(disabled_actions.get("execute"))
    return ""


def _derive_actions_from_semantic_page(
    *,
    semantic_page: Dict[str, Any],
    disabled_actions: Dict[str, Any],
) -> Dict[str, Any]:
    actions = _as_dict(semantic_page.get("actions"))

    def _collect(group_key: str) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for row in _as_list(actions.get(group_key)):
            item = _as_dict(row)
            action_key = _text(item.get("key"))
            if not action_key:
                continue
            if _infer_action_reason(item=item, disabled_actions=disabled_actions):
                continue
            rows.append(dict(item))
        return rows

    def _collect_semantic(*semantic_values: str) -> List[Dict[str, Any]]:
        matched: List[Dict[str, Any]] = []
        seen = set()
        semantic_set = {value.strip().lower() for value in semantic_values if value.strip()}
        for group_key in ("header_actions", "toolbar_actions", "record_actions"):
            for item in _collect(group_key):
                action_key = _text(item.get("key"))
                semantic = _text(item.get("semantic")).lower()
                if action_key in seen or semantic not in semantic_set:
                    continue
                matched.append(item)
                seen.add(action_key)
        return matched

    return {
        "primary_actions": _collect("header_actions"),
        "secondary_actions": _collect("toolbar_actions"),
        "contextual_actions": _collect("record_actions"),
        "danger_actions": _collect_semantic("danger", "destructive"),
        "recommended_actions": _collect_semantic("primary_action", "primary", "recommended"),
    }


def _derive_permissions_from_semantic_surface(surface: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = _as_dict(surface)
    permission_surface = _as_dict(payload.get("permission_surface"))
    workflow_surface = _as_dict(payload.get("workflow_surface"))
    validation_surface = _as_dict(payload.get("validation_surface"))
    semantic_page = _as_dict(payload.get("semantic_page"))
    if not permission_surface and not _workflow_surface_nonempty(workflow_surface) and not _validation_surface_nonempty(validation_surface):
        if not semantic_page:
            return {}

    visible = bool(permission_surface.get("visible", True))
    allowed = bool(permission_surface.get("allowed", True))
    reason_code = _text(permission_surface.get("reason_code"))
    record = _as_dict(payload.get("record"))
    runtime_state = _derive_semantic_runtime_state(
        permission_surface=permission_surface,
        workflow_surface=workflow_surface,
        validation_surface=validation_surface,
        semantic_page=semantic_page,
        record=record,
    )
    is_closed_state = bool(runtime_state.get("is_closed_state"))
    closed_reason = _text(runtime_state.get("closed_state_reason_code"))
    active_transitions = _as_list(runtime_state.get("active_transitions"))
    missing_required_fields = _as_list(runtime_state.get("missing_required_fields"))
    disabled_actions: Dict[str, Any] = {}
    if visible and not allowed:
        disabled_actions["edit"] = reason_code or "readonly"
        disabled_actions["create"] = reason_code or "readonly"
        disabled_actions["delete"] = reason_code or "readonly"
        if _workflow_surface_nonempty(workflow_surface):
            disabled_actions["workflow"] = "permission_workflow_gate"
    if is_closed_state:
        allowed = False
        disabled_actions["edit"] = closed_reason or "closed_state"
        disabled_actions["delete"] = closed_reason or "closed_state"
        disabled_actions["submit"] = closed_reason or "closed_state"
        if _workflow_surface_nonempty(workflow_surface):
            disabled_actions["workflow"] = closed_reason or "closed_state"
    if visible and allowed and missing_required_fields:
        disabled_actions["submit"] = "validation_required"

    record_state_summary = _derive_record_state_summary(
        workflow_surface,
        validation_surface,
        record,
        semantic_page,
        runtime_state=runtime_state,
    )
    if _workflow_surface_nonempty(workflow_surface):
        if visible and allowed and not active_transitions:
            disabled_actions["workflow"] = "action_permission_workflow_gate"
    flags = _apply_permission_verdicts(
        semantic_page=semantic_page,
        allowed=allowed,
        visible=visible,
        disabled_actions=disabled_actions,
    )
    _apply_action_semantics(semantic_page=semantic_page, disabled_actions=disabled_actions)
    return {
        "can_read": flags["can_read"],
        "can_edit": flags["can_edit"],
        "can_create": flags["can_create"],
        "can_delete": flags["can_delete"],
        "disabled_actions": disabled_actions,
        "record_state_summary": record_state_summary,
        "semantic_runtime_state": runtime_state,
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
    mapped_specs = map_zone_specs_to_blocks(zone_specs)
    ordered_specs = apply_zone_priority(mapped_specs, zone_order=zone_order)
    diagnostics_payload = dict(diagnostics or {})
    diagnostics_payload.setdefault("scene_engine", "smart_scene.core.scene_engine")
    diagnostics_payload.setdefault("zone_specs_mapped", ordered_specs)
    derived_permissions = _derive_permissions_from_semantic_surface(semantic_payload)
    semantic_payload["semantic_runtime_state"] = _as_dict((derived_permissions or {}).get("semantic_runtime_state"))
    resolved = resolve_scene_identity(scene_hint=scene_hint, page_hint=page_hint, semantic_surface=semantic_payload)
    derived_actions = _derive_actions_from_semantic_page(
        semantic_page=_as_dict(semantic_payload.get("semantic_page")),
        disabled_actions=_as_dict((derived_permissions or {}).get("disabled_actions")),
    )
    page_payload = dict(page_hint or {})
    lifecycle_display = _derive_lifecycle_display(_as_dict((derived_permissions or {}).get("record_state_summary")))
    if lifecycle_display:
        page_payload["lifecycle"] = lifecycle_display
    list_search_profile = _derive_list_search_profile(semantic_payload)
    if list_search_profile:
        page_payload["list_profile"] = list_search_profile
    relation_entries = _derive_relation_entries(semantic_payload)
    if relation_entries:
        page_payload["relation_entries"] = relation_entries
    diagnostics_payload["scene_envelope_observability"] = _build_scene_envelope_presence(
        semantic_payload=semantic_payload,
        page_payload=page_payload,
        derived_actions=derived_actions,
    )
    return build_scene_contract(
        scene=resolved.get("scene") or {},
        page={**(resolved.get("page") or {}), **page_payload},
        zones=built_zones,
        record=record or {},
        nav_ref=nav_ref or {
            "active_scene_key": str((resolved.get("scene") or {}).get("scene_key") or "").strip(),
            "active_menu_id": page_hint.get("menu_id") if isinstance(page_hint, dict) else None,
        },
        permissions=derived_permissions,
        actions=derived_actions,
        diagnostics=diagnostics_payload,
        semantic_surface=semantic_payload,
    )
