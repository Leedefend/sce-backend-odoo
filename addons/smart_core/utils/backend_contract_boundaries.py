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
VIEW_ORCHESTRATION_SOURCE_RUNTIME_VIEW_SNAPSHOT = "runtime_backend_form_view_contract"
MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING = "smart_core.lowcode.menu_config"
MENU_CONFIG_POLICY_MODEL = "ui.menu.config.policy"
MENU_CONFIG_RUNTIME_SOURCE_POLICY = "ui.menu.config.policy"
MENU_CONFIG_RUNTIME_SOURCE_CONTRACT = "ui.business.config.contract.menu_orchestration"
MENU_CONFIG_NAV_ENABLED_PARAM = "smart_core.nav.user_menu_config.enabled"
MENU_CONFIG_CONFIG_ONLY_PARAM = "smart_core.nav.user_menu_config.config_only.enabled"
NAV_USER_DATA_ACCEPTANCE_ONLY_PARAM = "smart_core.nav.user_data_acceptance_only"
APPROVAL_POLICY_SOURCE_TENANT_LOWCODING = "smart_core.lowcode.approval_policy"
APPROVAL_POLICY_RUNTIME_SOURCE = "sc.approval.policy"

LOWCODE_SOURCE_STATUS_DEVELOPER_DRAFT = "developer_draft"
LOWCODE_SOURCE_STATUS_TENANT_RUNTIME = "tenant_runtime"
LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE = "product_release"
LOWCODE_SOURCE_STATUSES = {
    LOWCODE_SOURCE_STATUS_DEVELOPER_DRAFT,
    LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
    LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE,
}
LOWCODE_SYSTEM_CONFIG_MENU_XMLIDS = frozenset()

BUSINESS_CONFIG_MODES = {
    "form_field": "form_field_configuration",
    "lowcode": "business_config_lowcode",
}

BUSINESS_CONFIG_ACTION_KEYS = {
    "current_form_field_settings": "current_form_field_settings",
    "current_form_add_custom_field": "current_form_add_custom_field",
    "current_form_field_order_save": "current_form_field_order_save",
    "current_form_field_configuration": "current_form_field_configuration",
}
BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_SETTINGS = BUSINESS_CONFIG_ACTION_KEYS["current_form_field_settings"]
BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_ADD_CUSTOM_FIELD = BUSINESS_CONFIG_ACTION_KEYS["current_form_add_custom_field"]
BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_ORDER_SAVE = BUSINESS_CONFIG_ACTION_KEYS["current_form_field_order_save"]
BUSINESS_CONFIG_ACTION_KEY_CURRENT_FORM_FIELD_CONFIGURATION = BUSINESS_CONFIG_ACTION_KEYS["current_form_field_configuration"]

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

FORM_FIELD_CONFIG_INTENTS = {
    "policy_set": "ui.form_field_policy.set",
    "custom_field_create": "ui.form_custom_field.create",
    "order_set": "ui.form_field_order.set",
    "batch_set": "ui.form_field_config.batch_set",
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
LAYER_USER_PREFERENCE = 15
LAYER_INDUSTRY_STANDARD = 20
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


def normalize_lowcode_source_status(value: Any, default: str = LOWCODE_SOURCE_STATUS_TENANT_RUNTIME) -> str:
    status = str(value or "").strip()
    if status in LOWCODE_SOURCE_STATUSES:
        return status
    return default


def view_orchestration_source_status(payload: Any) -> str:
    if not isinstance(payload, dict):
        return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE
    view_orchestration = payload.get("view_orchestration")
    if isinstance(view_orchestration, dict):
        context = view_orchestration.get("context")
        if isinstance(context, dict):
            status = normalize_lowcode_source_status(context.get("source_status"), default="")
            if status:
                return status
    source = _payload_source(payload).lower()
    if source.startswith("smart_core.lowcode.") or source in {
        VIEW_ORCHESTRATION_SOURCE_FIELD_POLICY,
        VIEW_ORCHESTRATION_SOURCE_ANALYSIS_EDITOR,
    }:
        return LOWCODE_SOURCE_STATUS_TENANT_RUNTIME
    return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE


def menu_orchestration_source_status(payload: Any) -> str:
    if not isinstance(payload, dict):
        return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE
    menu_orchestration = payload.get("menu_orchestration")
    if not isinstance(menu_orchestration, dict):
        return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE
    status = normalize_lowcode_source_status(menu_orchestration.get("source_status"), default="")
    if status:
        return status
    source = str(menu_orchestration.get("source") or "").strip()
    if source == MENU_ORCHESTRATION_SOURCE_TENANT_LOWCODING:
        return LOWCODE_SOURCE_STATUS_TENANT_RUNTIME
    return LOWCODE_SOURCE_STATUS_PRODUCT_RELEASE


def classify_view_orchestration_contract(name: Any, payload: Any = None) -> dict[str, Any]:
    contract_name = str(name or "").strip()
    source = _payload_source(payload)
    source_status = view_orchestration_source_status(payload)
    lower_name = contract_name.lower()
    lower_source = source.lower()
    legacy_user_flat = (
        lower_name.endswith(":custom_user_flat")
        or lower_name.endswith(".custom_user_flat")
        or ":custom_user_default" in lower_name
    )
    custom_user_source = (
        lower_source.endswith(".user_menu_preference")
        or lower_source.endswith(".user_view_preference")
        or lower_source.endswith(".user_form_preference")
        or lower_source.endswith(".partner_form_preference")
    )
    if legacy_user_flat or custom_user_source:
        return {
            "layer": LAYER_USER_PREFERENCE,
            "kind": "user_preference_projection",
            "source": source,
            "source_status": source_status,
            "compatibility": True,
        }
    if lower_source == VIEW_ORCHESTRATION_SOURCE_RUNTIME_VIEW_SNAPSHOT:
        return {
            "layer": LAYER_GENERATED_BASELINE,
            "kind": "generated_industry_baseline",
            "source": source,
            "source_status": source_status,
            "compatibility": False,
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
            "source_status": source_status,
            "compatibility": False,
        }
    if "_generated_" in lower_name or lower_name.endswith("_generated_v1"):
        return {
            "layer": LAYER_GENERATED_BASELINE,
            "kind": "generated_industry_baseline",
            "source": source,
            "source_status": source_status,
            "compatibility": False,
        }
    return {
        "layer": LAYER_INDUSTRY_STANDARD,
        "kind": "industry_standard_configuration",
        "source": source,
        "source_status": source_status,
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


def ensure_view_orchestration_source(
    payload: Any,
    source: str,
    source_status: str = LOWCODE_SOURCE_STATUS_TENANT_RUNTIME,
) -> dict:
    next_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    view_orchestration = next_payload.get("view_orchestration")
    if not isinstance(view_orchestration, dict):
        return next_payload
    next_orchestration = dict(view_orchestration)
    context = next_orchestration.get("context")
    next_context = dict(context or {}) if isinstance(context, dict) else {}
    next_context["source"] = str(source or "").strip()
    next_context["source_status"] = normalize_lowcode_source_status(source_status)
    next_orchestration["context"] = next_context
    next_payload["view_orchestration"] = next_orchestration
    return next_payload


def ensure_menu_orchestration_source_status(payload: Any, source_status: str = LOWCODE_SOURCE_STATUS_TENANT_RUNTIME) -> dict:
    next_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    menu_orchestration = next_payload.get("menu_orchestration")
    if not isinstance(menu_orchestration, dict):
        return next_payload
    next_orchestration = dict(menu_orchestration)
    next_orchestration["source_status"] = normalize_lowcode_source_status(source_status)
    next_payload["menu_orchestration"] = next_orchestration
    return next_payload


def ensure_lowcode_contract_source_status(payload: Any) -> dict:
    next_payload = dict(payload or {}) if isinstance(payload, dict) else {}
    view_orchestration = next_payload.get("view_orchestration")
    if isinstance(view_orchestration, dict):
        next_orchestration = dict(view_orchestration)
        context = next_orchestration.get("context")
        next_context = dict(context or {}) if isinstance(context, dict) else {}
        if not str(next_context.get("source_status") or "").strip():
            next_context["source_status"] = view_orchestration_source_status(next_payload)
            next_orchestration["context"] = next_context
            next_payload["view_orchestration"] = next_orchestration

    menu_orchestration = next_payload.get("menu_orchestration")
    if isinstance(menu_orchestration, dict):
        next_orchestration = dict(menu_orchestration)
        if not str(next_orchestration.get("source_status") or "").strip():
            next_orchestration["source_status"] = menu_orchestration_source_status(next_payload)
            next_payload["menu_orchestration"] = next_orchestration

    return next_payload
