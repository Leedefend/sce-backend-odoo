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

    return {
        "contract_version": "v1",
        "scene_channel": _as_text(data.get("scene_channel")) or "stable",
        "scene_contract_ref": _as_text(data.get("scene_contract_ref")),
        "runtime_source": _as_text(diagnostics.get("loaded_from")) or "unknown",
        "governance": governance,
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
        "diagnostics": {
            "normalize_warning_count": len(normalize_warnings),
            "resolve_error_count": len(resolve_errors),
            "drift_count": len(drift),
            "resolve_error_codes": resolve_error_codes,
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
