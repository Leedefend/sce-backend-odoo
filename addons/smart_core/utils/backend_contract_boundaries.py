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
MENU_CONFIG_POLICY_MODEL = "ui.menu.config.policy"
MENU_CONFIG_RUNTIME_SOURCE_POLICY = "ui.menu.config.policy"
MENU_CONFIG_RUNTIME_SOURCE_CONTRACT = "ui.business.config.contract.menu_orchestration"
MENU_CONFIG_NAV_ENABLED_PARAM = "smart_core.nav.user_menu_config.enabled"
MENU_CONFIG_CONFIG_ONLY_PARAM = "smart_core.nav.user_menu_config.config_only.enabled"
NAV_USER_DATA_ACCEPTANCE_ONLY_PARAM = "smart_core.nav.user_data_acceptance_only"
APPROVAL_POLICY_SOURCE_TENANT_LOWCODING = "smart_construction_core.lowcode.approval_policy"
APPROVAL_POLICY_RUNTIME_SOURCE = "sc.approval.policy"

BUSINESS_CONFIG_MODES = {
    "form_field": "form_field_configuration",
    "lowcode": "business_config_lowcode",
}

BUSINESS_CONFIG_AUTHORITIES = {
    "contract": "ui.business.config.contract",
    "contract_version": "ui.business.config.contract.version",
    "form_field_policy": "ui.form.field.policy",
    "custom_field_wizard": "ui.form.custom.field.wizard",
}

BUSINESS_CONFIG_OWNER_LAYER = "business_view_orchestration"

BUSINESS_CONFIG_INTENTS = {
    "form_audit": "ui.business_config.form.audit",
    "lowcode_apply": "ui.business_config.lowcode.apply",
    "contract_list": "ui.business_config.contract.list",
    "contract_get": "ui.business_config.contract.get",
    "contract_save": "ui.business_config.contract.save",
    "contract_publish": "ui.business_config.contract.publish",
    "contract_rollback": "ui.business_config.contract.rollback",
    "contract_versions": "ui.business_config.contract.versions",
    "list_search_audit": "ui.business_config.list_search.audit",
    "list_search_set": "ui.business_config.list_search.set",
    "list_search_bootstrap": "ui.business_config.list_search.bootstrap",
    "analysis_audit": "ui.business_config.analysis.audit",
    "analysis_set": "ui.business_config.analysis.set",
    "analysis_bootstrap": "ui.business_config.analysis.bootstrap",
    "form_bootstrap": "ui.business_config.form.bootstrap",
    "surface_get": "ui.business_config.surface.get",
    "snapshot_summary": "ui.business_config.snapshot.summary",
    "snapshot_export": "ui.business_config.snapshot.export",
    "snapshot_compare": "ui.business_config.snapshot.compare",
    "coverage_scan": "ui.business_config.coverage.scan",
    "coverage_bootstrap_list_search": "ui.business_config.coverage.bootstrap_list_search",
    "coverage_bootstrap_missing": "ui.business_config.coverage.bootstrap_missing",
}

MENU_CONFIG_INTENTS = {
    "panel_get": "ui.menu_config.panel.get",
    "panel_set": "ui.menu_config.panel.set",
    "menu_create": "ui.menu_config.menu.create",
    "menu_delete": "ui.menu_config.menu.delete",
    "audit": "ui.menu_config.audit",
    "rollback": "ui.menu_config.rollback",
    "versions": "ui.menu_config.versions",
}

APPROVAL_POLICY_INTENTS = {
    "config_get": "sc.approval_policy.config.get",
    "config_set": "sc.approval_policy.config.set",
    "steps_set": "sc.approval_policy.steps.set",
}

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
