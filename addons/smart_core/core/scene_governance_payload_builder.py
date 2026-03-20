# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict


def _as_text(value: Any) -> str:
    return str(value or "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return list(value) if isinstance(value, list) else []


def _error_codes(resolve_errors: list) -> list[str]:
    out: list[str] = []
    for item in resolve_errors:
        if not isinstance(item, dict):
            continue
        code = _as_text(item.get("code"))
        if code:
            out.append(code)
    seen: set[str] = set()
    unique: list[str] = []
    for code in out:
        if code in seen:
            continue
        seen.add(code)
        unique.append(code)
    return unique


def _scene_type_consumption_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    ready = _as_dict(data.get("scene_ready_contract_v1"))
    ready_meta = _as_dict(ready.get("meta"))
    metrics = _as_dict(ready_meta.get("scene_type_consumption_metrics"))
    if not metrics:
        return {
            "enabled": False,
            "scene_type_count": 0,
            "scene_count": 0,
            "scene_types": {},
            "aggregate": {
                "base_fact_consumption_rate": {},
                "surface_nonempty_rate": {},
            },
        }

    aggregate_base = {"search": 0.0, "workflow": 0.0, "validator": 0.0, "actions": 0.0}
    aggregate_surface = {"search": 0.0, "workflow": 0.0, "validation": 0.0, "action_surface": 0.0}
    scene_count = 0
    scene_types: Dict[str, Any] = {}
    for scene_type, row in metrics.items():
        payload = _as_dict(row)
        count = int(payload.get("scene_count") or 0)
        scene_count += max(count, 0)
        base_rate = _as_dict(payload.get("base_fact_consumption_rate"))
        surface_rate = _as_dict(payload.get("surface_nonempty_rate"))
        scene_types[_as_text(scene_type)] = {
            "scene_count": count,
            "base_fact_consumption_rate": {
                "search": float(base_rate.get("search") or 0.0),
                "workflow": float(base_rate.get("workflow") or 0.0),
                "validator": float(base_rate.get("validator") or 0.0),
                "actions": float(base_rate.get("actions") or 0.0),
            },
            "surface_nonempty_rate": {
                "search": float(surface_rate.get("search") or 0.0),
                "workflow": float(surface_rate.get("workflow") or 0.0),
                "validation": float(surface_rate.get("validation") or 0.0),
                "action_surface": float(surface_rate.get("action_surface") or 0.0),
            },
        }
        aggregate_base["search"] += float(base_rate.get("search") or 0.0) * float(max(count, 0))
        aggregate_base["workflow"] += float(base_rate.get("workflow") or 0.0) * float(max(count, 0))
        aggregate_base["validator"] += float(base_rate.get("validator") or 0.0) * float(max(count, 0))
        aggregate_base["actions"] += float(base_rate.get("actions") or 0.0) * float(max(count, 0))
        aggregate_surface["search"] += float(surface_rate.get("search") or 0.0) * float(max(count, 0))
        aggregate_surface["workflow"] += float(surface_rate.get("workflow") or 0.0) * float(max(count, 0))
        aggregate_surface["validation"] += float(surface_rate.get("validation") or 0.0) * float(max(count, 0))
        aggregate_surface["action_surface"] += float(surface_rate.get("action_surface") or 0.0) * float(max(count, 0))

    denom = float(scene_count) if scene_count > 0 else 1.0
    return {
        "enabled": True,
        "scene_type_count": len(scene_types),
        "scene_count": scene_count,
        "scene_types": scene_types,
        "aggregate": {
            "base_fact_consumption_rate": {
                "search": aggregate_base["search"] / denom,
                "workflow": aggregate_base["workflow"] / denom,
                "validator": aggregate_base["validator"] / denom,
                "actions": aggregate_base["actions"] / denom,
            },
            "surface_nonempty_rate": {
                "search": aggregate_surface["search"] / denom,
                "workflow": aggregate_surface["workflow"] / denom,
                "validation": aggregate_surface["validation"] / denom,
                "action_surface": aggregate_surface["action_surface"] / denom,
            },
        },
    }


def _governance_surface_mapping(
    governance: Dict[str, Any],
    nav_policy: Dict[str, Any],
    delivery_policy: Dict[str, Any],
) -> Dict[str, Any]:
    before = _as_dict(governance.get("before"))
    after = _as_dict(governance.get("after"))
    filtered = _as_dict(governance.get("filtered"))

    before_scene_count = int(before.get("scene_count") or 0)
    after_scene_count = int(after.get("scene_count") or 0)
    before_capability_count = int(before.get("capability_count") or 0)
    after_capability_count = int(after.get("capability_count") or 0)

    removed_scene_count = int(filtered.get("scene_count") or max(before_scene_count - after_scene_count, 0))
    removed_capability_count = int(filtered.get("capability_count") or max(before_capability_count - after_capability_count, 0))

    removed_scene_codes: list[str] = []
    for row in _as_list(nav_policy.get("excluded_scenes_sample")):
        item = _as_dict(row)
        code = _as_text(item.get("code"))
        if code and code not in removed_scene_codes:
            removed_scene_codes.append(code)
    if not removed_scene_codes:
        for row in _as_list(delivery_policy.get("excluded_scenes")):
            item = _as_dict(row)
            code = _as_text(item.get("code"))
            if code and code not in removed_scene_codes:
                removed_scene_codes.append(code)

    return {
        "before": {
            "scene_count": before_scene_count,
            "capability_count": before_capability_count,
        },
        "after": {
            "scene_count": after_scene_count,
            "capability_count": after_capability_count,
        },
        "removed": {
            "scene_count": removed_scene_count,
            "capability_count": removed_capability_count,
            "scene_codes_sample": removed_scene_codes[:20],
        },
    }


def build_scene_governance_payload_v1(
    *,
    data: Dict[str, Any],
    scene_diagnostics: Dict[str, Any] | None,
    delivery_meta: Dict[str, Any] | None,
    nav_contract_meta: Dict[str, Any] | None,
    asset_queue_metrics: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    diagnostics = _as_dict(scene_diagnostics)
    governance = _as_dict(diagnostics.get("governance"))
    auto_degrade = _as_dict(diagnostics.get("auto_degrade"))
    role_surface_provider = _as_dict(diagnostics.get("role_surface_provider"))
    delivery_policy = _as_dict(delivery_meta)
    nav_policy = _as_dict(nav_contract_meta)
    normalize_warnings = _as_list(diagnostics.get("normalize_warnings"))
    resolve_errors = _as_list(diagnostics.get("resolve_errors"))
    drift = _as_list(diagnostics.get("drift"))
    queue_metrics = _as_dict(asset_queue_metrics)

    nav_policy_validation_ok = bool(nav_policy.get("nav_policy_validation_ok", False))
    delivery_policy_applied = bool(delivery_policy.get("enabled", False))
    resolve_error_codes = _error_codes(resolve_errors)
    auto_degrade_reason_codes = [
        _as_text(code)
        for code in _as_list(auto_degrade.get("reason_codes"))
        if _as_text(code)
    ]
    consumption_summary = _scene_type_consumption_summary(data)
    surface_mapping = _governance_surface_mapping(governance, nav_policy, delivery_policy)

    return {
        "contract_version": "v1",
        "scene_channel": _as_text(data.get("scene_channel")) or "stable",
        "scene_contract_ref": _as_text(data.get("scene_contract_ref")),
        "runtime_source": _as_text(diagnostics.get("loaded_from")) or "unknown",
        "governance": governance,
        "surface_mapping": surface_mapping,
        "auto_degrade": auto_degrade,
        "delivery_policy": delivery_policy,
        "nav_policy": {
            "validation_ok": nav_policy_validation_ok,
            "source": _as_text(nav_policy.get("nav_policy_source")),
            "provider": _as_text(nav_policy.get("nav_policy_provider")),
            "version": _as_text(nav_policy.get("nav_policy_version")),
            "issues": _as_list(nav_policy.get("nav_policy_validation_issues")),
        },
        "role_surface_provider": role_surface_provider,
        "asset_queue": {
            "queue_size": int(queue_metrics.get("queue_size") or 0),
            "updated_at": _as_text(queue_metrics.get("updated_at")),
            "reason": _as_text(queue_metrics.get("reason")),
            "added_count": int(queue_metrics.get("added_count") or 0),
            "last_operation": _as_text(queue_metrics.get("last_operation")),
            "consumed_at": _as_text(queue_metrics.get("consumed_at")),
            "popped_count": int(queue_metrics.get("popped_count") or 0),
            "remaining_count": int(queue_metrics.get("remaining_count") or 0),
        },
        "scene_ready_consumption": consumption_summary,
        "diagnostics": {
            "normalize_warning_count": len(normalize_warnings),
            "resolve_error_count": len(resolve_errors),
            "drift_count": len(drift),
            "resolve_error_codes": resolve_error_codes,
            "scene_ready_consumption_enabled": bool(consumption_summary.get("enabled", False)),
        },
        "gates": {
            "orchestrator_applied": bool(_as_text(data.get("scene_contract_ref"))),
            "governance_applied": bool(governance),
            "delivery_policy_applied": delivery_policy_applied,
            "nav_policy_validation_ok": nav_policy_validation_ok,
            "auto_degrade_triggered": bool(auto_degrade.get("triggered", False)),
        },
        "reasons": {
            "auto_degrade_reason_codes": auto_degrade_reason_codes,
            "resolve_error_codes": resolve_error_codes,
        },
    }
