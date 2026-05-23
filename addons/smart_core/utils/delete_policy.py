# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, Iterable

from .extension_hooks import call_extension_hook_first


DELETE_POLICY_ALLOWED = "DELETE_POLICY_ALLOWED"
DELETE_POLICY_DENIED = "DELETE_POLICY_DENIED"
SOURCE_KIND = "unlink_policy_projection"
SOURCE_AUTHORITIES = ("extension_unlink_policy", "handler_default_allowlist", "odoo_access_control")
NO_BUSINESS_FACT_AUTHORITY = True


def source_authority_contract() -> Dict[str, Any]:
    return {
        "kind": SOURCE_KIND,
        "authorities": list(SOURCE_AUTHORITIES),
        "projection_only": True,
        "no_business_fact_authority": NO_BUSINESS_FACT_AUTHORITY,
        "default_behavior": "deny_unless_extension_or_handler_default_allows",
    }


def _as_model_set(values: Iterable[Any] | None) -> set[str]:
    return {str(item).strip() for item in (values or []) if str(item).strip()}


def _normalize_policy(model: str, raw: Any, *, source: str) -> Dict[str, Any]:
    row = dict(raw) if isinstance(raw, dict) else {}
    delete_mode = str(row.get("delete_mode") or row.get("mode") or "").strip().lower()
    allowed = row.get("allowed")
    if allowed is None:
        allowed = delete_mode in {"unlink", "archive"}
    allowed = bool(allowed)
    if not delete_mode:
        delete_mode = "unlink" if allowed else "none"
    reason_code = str(row.get("reason_code") or "").strip()
    if not reason_code:
        reason_code = DELETE_POLICY_ALLOWED if allowed else DELETE_POLICY_DENIED
    message = str(row.get("message") or "").strip()
    if not message:
        message = "允许删除" if allowed else "当前模型未开放删除"
    normalized = {
        "model": model,
        "allowed": allowed,
        "delete_mode": delete_mode if allowed else "none",
        "reason_code": reason_code,
        "message": message,
        "source": str(row.get("source") or source or "delete_policy").strip(),
        "source_authority": source_authority_contract(),
        "requires_acl": bool(row.get("requires_acl", True)),
        "requires_record_rule": bool(row.get("requires_record_rule", True)),
        "dry_run_supported": True,
    }
    for key in (
        "policy_kind",
        "state_field",
        "requires_group",
        "dependency_guard",
    ):
        value = str(row.get(key) or "").strip()
        if value:
            normalized[key] = value
    for key in ("allowed_states", "blocked_states"):
        values = sorted(_as_model_set(row.get(key)))
        if values:
            normalized[key] = values
    return normalized


def _normalize_policy_payload(payload: Any, *, default_allowed_models: Iterable[str] | None = None) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for model in _as_model_set(default_allowed_models):
        out[model] = _normalize_policy(model, {"allowed": True, "delete_mode": "unlink"}, source="handler_default")
    if isinstance(payload, (list, tuple, set)):
        for model in _as_model_set(payload):
            out[model] = _normalize_policy(model, {"allowed": True, "delete_mode": "unlink"}, source="extension_allowlist")
        return out
    if not isinstance(payload, dict):
        return out
    models = payload.get("models") if isinstance(payload.get("models"), dict) else payload
    for model_raw, policy_raw in models.items():
        model = str(model_raw or "").strip()
        if not model:
            continue
        out[model] = _normalize_policy(model, policy_raw, source="extension_policy")
    return out


def unlink_policy_map(env, *, default_allowed_models: Iterable[str] | None = None) -> Dict[str, Dict[str, Any]]:
    payload = call_extension_hook_first(env, "smart_core_api_data_unlink_allowed_models", env)
    return _normalize_policy_payload(payload, default_allowed_models=default_allowed_models)


def resolve_unlink_policy(env, model: str, *, default_allowed_models: Iterable[str] | None = None) -> Dict[str, Any]:
    model_name = str(model or "").strip()
    policies = unlink_policy_map(env, default_allowed_models=default_allowed_models)
    if model_name in policies:
        return dict(policies[model_name])
    return _normalize_policy(
        model_name,
        {
            "allowed": False,
            "delete_mode": "none",
            "reason_code": DELETE_POLICY_DENIED,
            "message": "当前模型未开放删除",
        },
        source="delete_policy_default_denied",
    )
