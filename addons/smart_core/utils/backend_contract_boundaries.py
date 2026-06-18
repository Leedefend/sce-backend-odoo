# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any


BUSINESS_CONFIG_RUNTIME_MODELS = {
    "sc.approval.policy",
    "sc.approval.step",
    "sc.approval.scope",
    "sc.approval.scope.user.wizard",
    "ui.business.config.contract",
    "ui.form.field.policy",
    "ui.form.custom.field.wizard",
    "ui.menu.config.policy",
}

VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING = "smart_core.lowcode.business_config"
VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY = "smart_core.lowcode.form_field_policy"
VIEW_ORCHESTRATION_SOURCE_ANALYSIS_EDITOR = "business_config_analysis_editor"
MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING = "smart_core.lowcode.menu_config"
APPROVAL_POLICY_SOURCE_TENANT_LOWCODING = "smart_construction_core.lowcode.approval_policy"
APPROVAL_POLICY_RUNTIME_SOURCE = "sc.approval.policy"

LAYER_GENERATED_BASELINE = 10
LAYER_INDUSTRY_STANDARD = 20
LAYER_USER_PREFERENCE = 30
LAYER_TENANT_LOWCODING = 40


def is_business_config_runtime_model(model: Any) -> bool:
    return str(model or "").strip() in BUSINESS_CONFIG_RUNTIME_MODELS


def _payload_source(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    view_orchestration = payload.get("view_orchestration")
    if isinstance(view_orchestration, dict):
        context = view_orchestration.get("context")
        if isinstance(context, dict):
            source = str(context.get("source") or "").strip()
            if source:
                return source
    return str(payload.get("source") or "").strip()


def classify_view_orchestration_contract(name: Any, payload: Any = None) -> dict[str, Any]:
    contract_name = str(name or "").strip()
    source = _payload_source(payload)
    lower_name = contract_name.lower()
    lower_source = source.lower()
    legacy_user_flat = (
        lower_name.endswith(":custom_user_flat")
        or lower_name.endswith(".custom_user_flat")
        or ":custom_user_default" in lower_name
    )
    custom_user_source = lower_source.startswith("smart_construction_custom.") and "preference" in lower_source
    if legacy_user_flat or custom_user_source:
        return {
            "layer": LAYER_USER_PREFERENCE,
            "kind": "user_preference_projection",
            "source": source,
            "compatibility": True,
        }
    if (
        lower_source
        in {
            VIEW_ORCHESTRATION_SOURCE_TENANT_LOWCODING,
            VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY,
            VIEW_ORCHESTRATION_SOURCE_ANALYSIS_EDITOR,
        }
        or lower_name.startswith("view_orchestration:")
    ):
        return {
            "layer": LAYER_TENANT_LOWCODING,
            "kind": "tenant_lowcode_configuration",
            "source": source,
            "compatibility": False,
        }
    if "_generated_" in lower_name or lower_name.endswith("_generated_v1"):
        return {
            "layer": LAYER_GENERATED_BASELINE,
            "kind": "generated_industry_baseline",
            "source": source,
            "compatibility": False,
        }
    return {
        "layer": LAYER_INDUSTRY_STANDARD,
        "kind": "industry_standard_configuration",
        "source": source,
        "compatibility": False,
    }


def view_orchestration_apply_order_key(contract: Any) -> tuple:
    payload = getattr(contract, "contract_json", {}) or {}
    boundary = classify_view_orchestration_contract(getattr(contract, "name", ""), payload)
    action_specific = 1 if int(getattr(getattr(contract, "action_id", None), "id", 0) or 0) else 0
    view_specific = 1 if int(getattr(getattr(contract, "view_id", None), "id", 0) or 0) else 0
    role_specific = 1 if str(getattr(contract, "role_key", "") or "").strip() else 0
    return (
        int(boundary["layer"]),
        action_specific,
        view_specific,
        role_specific,
        int(getattr(contract, "priority", 100) or 100),
        int(getattr(contract, "version_no", 1) or 1),
        int(getattr(contract, "id", 0) or 0),
    )


def ensure_view_orchestration_source(payload: Any, source: str) -> dict:
    next_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    view_orchestration = next_payload.get("view_orchestration")
    if not isinstance(view_orchestration, dict):
        return next_payload
    next_orchestration = dict(view_orchestration)
    context = next_orchestration.get("context")
    next_context = dict(context or {}) if isinstance(context, dict) else {}
    next_context["source"] = str(source or "").strip()
    next_orchestration["context"] = next_context
    next_payload["view_orchestration"] = next_orchestration
    return next_payload
