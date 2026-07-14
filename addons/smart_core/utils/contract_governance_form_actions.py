# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable


_RENDER_PROFILE_CREATE = "create"
_RENDER_PROFILE_EDIT = "edit"
_RENDER_PROFILE_READONLY = "readonly"
_RENDER_PROFILES = {_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY}
_FORM_ACTION_PRIMARY_KEYWORDS: tuple[str, ...] = ()
_FORM_ACTION_READONLY_KEYWORDS: tuple[str, ...] = ()
_FORM_PRIMARY_DISABLED_REASON = ""
_FORM_DISABLED_REASON_CAPABILITY = ""
_FORM_DISABLED_REASON_LIFECYCLE = ""
_FORM_DISABLED_REASON_GROUP = ""
_FORM_DISABLED_REASON_ROLE = ""
_FORM_SCENE_PROFILE_PROJECT = "project"


def _safe_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    if text.lower() in {"undefined", "null"}:
        text = ""
    return text or fallback


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _as_dict(value: Any) -> dict:
    return dict(value) if isinstance(value, dict) else {}


def infer_action_semantic(action: dict) -> str:
    label = _safe_lower(action.get("label"))
    key = _safe_lower(action.get("key"))
    merged = f"{label} {key}"
    if any(keyword in merged for keyword in _FORM_ACTION_PRIMARY_KEYWORDS):
        return "primary_action"
    if any(keyword in merged for keyword in ("删除", "停用", "archive", "unlink", "删除")):
        return "danger"
    return "secondary"


def infer_visible_profiles(action: dict) -> list[str]:
    label = _safe_lower(action.get("label"))
    key = _safe_lower(action.get("key"))
    merged = f"{label} {key}"
    if any(keyword in merged for keyword in ("创建", "提交", "create", "submit")):
        return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]
    if any(keyword in merged for keyword in ("编辑", "修改", "edit", "write")):
        return [_RENDER_PROFILE_EDIT]
    if any(keyword in merged for keyword in _FORM_ACTION_READONLY_KEYWORDS):
        return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT, _RENDER_PROFILE_READONLY]
    return [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]


def annotate_form_actions(data: dict, *, is_form_contract: Callable[[dict], bool]) -> None:
    if not is_form_contract(data):
        return
    buttons = data.get("buttons")
    if not isinstance(buttons, list):
        return
    primary_assigned = False
    for row in buttons:
        if not isinstance(row, dict):
            continue
        semantic = _safe_text(row.get("semantic")).lower() or infer_action_semantic(row)
        if semantic == "primary_action":
            if primary_assigned:
                semantic = "secondary"
            else:
                primary_assigned = True
        row["semantic"] = semantic
        raw_profiles = row.get("visible_profiles")
        if isinstance(raw_profiles, list) and raw_profiles:
            profiles = [
                _safe_text(item).lower()
                for item in raw_profiles
                if _safe_text(item).lower() in _RENDER_PROFILES
            ]
        else:
            profiles = infer_visible_profiles(row)
        row["visible_profiles"] = profiles or [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT]


def default_action_policy(semantic: str, visible_profiles: list[str], required_fields: list[str]) -> dict[str, Any]:
    policy = {
        "visible_profiles": visible_profiles or [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
        "enabled_when": {},
        "disabled_reason": "",
        "semantic": semantic,
    }
    if semantic == "primary_action":
        policy["enabled_when"] = {
            "required_fields": required_fields[:12],
            "profiles": [_RENDER_PROFILE_CREATE, _RENDER_PROFILE_EDIT],
            "conditions": [],
        }
        policy["disabled_reason"] = _FORM_PRIMARY_DISABLED_REASON
    return policy


def resolve_action_policy_template_keys(
    *,
    scene_profile: str,
    semantic: str,
    required_capabilities: list[str],
    required_groups: list[str],
    required_roles: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
) -> list[str]:
    keys: list[str] = []
    if semantic == "primary_action":
        keys.append("base.primary")
    else:
        keys.append("base.secondary")
    if required_capabilities or required_groups or required_roles or (lifecycle_field and lifecycle_blocked_states):
        keys.append("constraint.access")
    if scene_profile == _FORM_SCENE_PROFILE_PROJECT and semantic == "primary_action":
        keys.append("scene.project.form.primary")
    return keys


def apply_action_policy_templates(
    policy: dict[str, Any],
    template_keys: list[str],
    *,
    required_fields: list[str],
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
    fields_map: dict[str, Any],
) -> None:
    def _apply_base_primary() -> None:
        base = default_action_policy("primary_action", policy.get("visible_profiles") or [], required_fields)
        policy["enabled_when"] = base.get("enabled_when") or {}
        policy["disabled_reason"] = base.get("disabled_reason") or policy.get("disabled_reason") or ""
        policy["semantic"] = "primary_action"

    def _apply_base_secondary() -> None:
        base = default_action_policy(
            _safe_text(policy.get("semantic"), "secondary"),
            policy.get("visible_profiles") or [],
            required_fields,
        )
        policy["enabled_when"] = base.get("enabled_when") or {}
        policy["disabled_reason"] = base.get("disabled_reason") or policy.get("disabled_reason") or ""

    def _apply_constraint_access() -> None:
        merge_policy_constraints(
            policy,
            required_capabilities=required_capabilities,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
            required_groups=required_groups,
            required_roles=required_roles,
        )

    def _apply_scene_project_primary() -> None:
        append_primary_action_conditions(policy, fields_map)

    template_registry = {
        "base.primary": _apply_base_primary,
        "base.secondary": _apply_base_secondary,
        "constraint.access": _apply_constraint_access,
        "scene.project.form.primary": _apply_scene_project_primary,
    }
    for key in template_keys:
        runner = template_registry.get(key)
        if callable(runner):
            runner()


def merge_policy_constraints(
    policy: dict[str, Any],
    *,
    required_capabilities: list[str],
    lifecycle_field: str,
    lifecycle_blocked_states: list[str],
    required_groups: list[str],
    required_roles: list[str],
) -> None:
    enabled_when = policy.get("enabled_when")
    if not isinstance(enabled_when, dict):
        enabled_when = {}

    if required_capabilities:
        enabled_when["required_capabilities"] = required_capabilities
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_CAPABILITY
    if lifecycle_field and lifecycle_blocked_states:
        enabled_when["lifecycle"] = {"field": lifecycle_field, "disallow_states": lifecycle_blocked_states}
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_LIFECYCLE
    if required_groups:
        enabled_when["required_groups"] = required_groups
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_GROUP
    if required_roles:
        enabled_when["required_roles"] = required_roles
        if not policy.get("disabled_reason"):
            policy["disabled_reason"] = _FORM_DISABLED_REASON_ROLE
    policy["enabled_when"] = enabled_when


def append_primary_action_conditions(policy: dict[str, Any], fields_map: dict[str, Any]) -> None:
    if _safe_text(policy.get("semantic")) != "primary_action":
        return
    enabled_when = policy.get("enabled_when")
    if not isinstance(enabled_when, dict):
        enabled_when = {"conditions": []}
    conditions = enabled_when.get("conditions")
    if not isinstance(conditions, list):
        conditions = []
    if "phase_key" in fields_map:
        conditions.append({"source": "record", "field": "phase_key", "op": "not_in", "value": ["archive"]})
    if "stage_id" in fields_map:
        conditions.append({"source": "record", "field": "stage_id", "op": "truthy"})
    enabled_when["conditions"] = conditions
    if conditions:
        enabled_when["condition_expr"] = {"op": "and", "items": [item for item in conditions if isinstance(item, dict)]}
    policy["enabled_when"] = enabled_when


def build_form_action_policies(
    data: dict,
    *,
    required_fields: list[str],
    scene_profile: str,
) -> dict[str, dict[str, Any]]:
    policies: dict[str, dict[str, Any]] = {}
    buttons = data.get("buttons")
    if not isinstance(buttons, list):
        return policies
    lifecycle_field = ""
    lifecycle_blocked_states: list[str] = []
    fields_map = _as_dict(data.get("fields"))
    lifecycle_desc = _as_dict(fields_map.get("lifecycle_state"))
    if lifecycle_desc:
        lifecycle_field = "lifecycle_state"
        selection = lifecycle_desc.get("selection")
        rows = selection if isinstance(selection, list) else []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            key = _safe_text(row[0]).lower()
            label = _safe_text(row[1]).lower()
            merged = f"{key} {label}"
            if any(token in merged for token in ("close", "closed", "done", "archive", "竣工", "关闭", "归档")):
                lifecycle_blocked_states.append(_safe_text(row[0]))
    for row in buttons:
        if not isinstance(row, dict):
            continue
        key = _safe_text(row.get("key"))
        if not key:
            continue
        semantic = _safe_text(row.get("semantic"), "secondary")
        visible_profiles = row.get("visible_profiles") if isinstance(row.get("visible_profiles"), list) else []
        normalized_visible = [
            _safe_text(item).lower()
            for item in visible_profiles
            if _safe_text(item).lower() in _RENDER_PROFILES
        ]
        policy = default_action_policy(semantic, normalized_visible, required_fields)
        row_groups = row.get("groups_xmlids") if isinstance(row.get("groups_xmlids"), list) else []
        required_groups = [
            _safe_text(item)
            for item in row_groups
            if _safe_text(item)
        ]
        required_roles_raw = row.get("required_roles") if isinstance(row.get("required_roles"), list) else []
        required_roles = [
            _safe_text(item).lower()
            for item in required_roles_raw
            if _safe_text(item)
        ]
        required_capabilities = row.get("required_capabilities")
        if not isinstance(required_capabilities, list):
            required_capabilities = row.get("capabilities")
        required_capabilities = [
            _safe_text(item)
            for item in (required_capabilities if isinstance(required_capabilities, list) else [])
            if _safe_text(item)
        ]
        template_keys = resolve_action_policy_template_keys(
            scene_profile=scene_profile,
            semantic=semantic,
            required_capabilities=required_capabilities,
            required_groups=required_groups,
            required_roles=required_roles,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
        )
        apply_action_policy_templates(
            policy,
            template_keys,
            required_fields=required_fields,
            required_capabilities=required_capabilities,
            lifecycle_field=lifecycle_field,
            lifecycle_blocked_states=lifecycle_blocked_states,
            required_groups=required_groups,
            required_roles=required_roles,
            fields_map=fields_map,
        )
        policies[key] = policy
    return policies
