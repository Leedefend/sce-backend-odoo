# -*- coding: utf-8 -*-
import logging

from odoo.addons.smart_construction_core.core_extension_bootstrap import apply_core_extension_bootstrap
from odoo.addons.smart_construction_core.core_extension_contract_projection import (
    smart_core_finalize_unified_page_contract_v2,
    smart_core_normalize_projected_contract_data,
    smart_core_normalize_unified_page_contract_v2,
)
from odoo.addons.smart_construction_core.core_extension_capabilities import (
    build_capability_contribution_item,
)
from odoo.addons.smart_construction_core.core_extension_form_actions import (
    build_payment_form_business_action_contract,
)
from odoo.addons.smart_construction_core.core_extension_intents import (
    get_intent_handler_contributions,
)
from odoo.addons.smart_construction_core.core_extension_system_init import (
    apply_system_init_profile_overrides,
)
from odoo.addons.smart_construction_core.core_extension_navigation_policy import (
    smart_core_business_config_admin_group_xmlids,
    smart_core_business_config_form_settings_refs,
    smart_core_business_config_approval_policy_refs,
    smart_core_native_config_root_menu_xmlid,
    smart_core_native_config_delivery_excluded_menu_xmlids,
    smart_core_lowcode_system_config_menu_xmlids,
    smart_core_lowcode_config_recovery_parent_menu_xmlids,
    smart_core_business_root_menu_xmlid,
    smart_core_relation_entry_policy,
    smart_core_model_specific_form_contract_policy,
    smart_core_form_field_aliases,
    smart_core_menu_delivery_token_policy,
    smart_core_business_nav_group_display_order,
    smart_core_product_policy_catalog_source,
    smart_core_product_policy_catalog_base_keys,
    smart_core_default_product_policy_specs,
    smart_core_product_policy_catalog_label,
    smart_core_platform_legacy_ownership_module,
    smart_core_resolve_release_actor_role_codes,
    smart_core_resolve_usage_actor_role_codes,
    smart_core_default_release_snapshot_role_code,
    smart_core_industry_extension_module_names,
    smart_core_app_shell_contract,
    smart_core_scene_entry_orchestrator_specs,
    smart_core_user_data_acceptance_nav_contract,
)
from odoo.addons.smart_construction_core.core_extension_workspace_facts import (
    _build_enterprise_enablement_contract,
    _build_home_block_contract_rows,
    _build_payment_action_rows,
    _build_project_action_rows,
    _build_risk_action_rows,
    _build_role_entry_contract_rows,
    _build_task_action_rows,
)
from odoo.addons.smart_construction_core.core_extension_services import (
    smart_core_scene_package_service_class,
    smart_core_scene_governance_service_class,
    smart_core_describe_project_capabilities,
    smart_core_build_portal_dashboard,
    smart_core_build_capability_matrix,
    smart_core_get_project_insight,
    smart_core_build_portal_execute_button_contract,
    smart_core_build_project_execution_service,
    smart_core_build_project_dashboard_service,
    smart_core_build_project_plan_bootstrap_service,
    smart_core_build_cost_tracking_service,
    smart_core_build_payment_slice_service,
    smart_core_build_settlement_slice_service,
)
from odoo.addons.smart_construction_core.core_extension_projected_contracts import (
    smart_core_finalize_projected_contract_data,
)
from odoo.addons.smart_construction_core.core_extension_api_policy import (
    get_api_data_create_execution_policy_contribution,
    get_api_data_mutation_policy_contribution,
    get_api_data_unlink_allowed_model_contributions,
    get_api_data_write_allowlist_contributions,
    get_file_download_allowed_model_contributions,
    get_file_upload_allowed_model_contributions,
    get_intent_permission_model_acl_policy_contribution,
    get_model_code_mapping_contributions,
    get_server_action_window_map_contributions,
    smart_core_api_data_create_execution_policy,
    smart_core_api_data_mutation_policy,
    smart_core_api_data_search_fields,
    smart_core_api_data_unlink_allowed_models,
    smart_core_api_data_write_allowlist,
    smart_core_file_download_allowed_models,
    smart_core_file_download_auth_subject,
    smart_core_file_upload_allowed_models,
    smart_core_intent_permission_model_acl_policy,
    smart_core_legacy_visible_business_column_labels,
    smart_core_model_code_mapping,
    smart_core_server_action_window_map,
)
from odoo.addons.smart_construction_core.core_extension_policy_catalog import (
    CRITICAL_SCENE_TARGET_OVERRIDES,
    CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES,
    INDUSTRY_CREATE_FIELD_FALLBACKS,
    NAV_ACTION_SCENE_MAP,
    NAV_MENU_SCENE_MAP,
    NAV_MODEL_VIEW_SCENE_MAP,
    ROLE_GROUPS_CAPABILITY_FALLBACK,
    ROLE_GROUPS_EXPLICIT,
    ROLE_PRECEDENCE,
    ROLE_SURFACE_OVERRIDES,
)

_logger = logging.getLogger(__name__)

apply_core_extension_bootstrap()

def smart_core_identity_profile(env):
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_nav_scene_maps(env):
    return {
        "menu_scene_map": dict(NAV_MENU_SCENE_MAP),
        "action_xmlid_scene_map": dict(NAV_ACTION_SCENE_MAP),
        "model_view_scene_map": dict(NAV_MODEL_VIEW_SCENE_MAP),
    }


def smart_core_surface_aliases(env):
    del env
    return {
        "construction_pm_v1": "workspace_default_v1",
    }


def smart_core_runtime_business_config_productization_sources(env):
    del env
    return [
        "smart_construction_custom.user_menu_preference",
    ]


def smart_core_resolve_record_context_config(env, params):
    del env, params
    return {
        "model": "project.project",
        "label": "当前项目",
        "placeholder": "搜索项目名称",
        "selected_id_param": "selected_id",
    }


def smart_core_critical_scene_target_overrides(env):
    return set(CRITICAL_SCENE_TARGET_OVERRIDES)


def smart_core_critical_scene_target_route_overrides(env):
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def smart_core_register(registry):
    """Compatibility loader for smart_core.core.extension_loader."""
    if not isinstance(registry, dict):
        return
    try:
        from odoo.addons.smart_construction_core.handlers.project_dashboard import (
            ProjectDashboardHandler,
        )

        registry["project.dashboard"] = ProjectDashboardHandler
    except Exception as exc:
        _logger.warning("[smart_core_register] skip project.dashboard explicit registration: %s", exc)
    for item in get_intent_handler_contributions():
        if not isinstance(item, dict):
            continue
        intent_name = str(item.get("intent") or "").strip()
        handler = item.get("handler")
        if intent_name and handler is not None:
            registry[intent_name] = handler


def get_capability_contributions(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user as registry_list_capabilities_for_user,
        )
    except Exception:
        return []
    try:
        capabilities = registry_list_capabilities_for_user(env, user)
    except Exception:
        return []
    if not isinstance(capabilities, list) or not capabilities:
        return []

    out = []
    for row in capabilities:
        item = build_capability_contribution_item(row)
        if item:
            out.append(item)
    return out


def get_capability_contributions_with_timings(env, user):
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import (
            list_capabilities_for_user_with_timings as registry_list_capabilities_for_user_with_timings,
        )
    except Exception:
        return [], {}
    try:
        capabilities, timings_ms = registry_list_capabilities_for_user_with_timings(env, user)
    except Exception:
        return [], {}
    if not isinstance(capabilities, list) or not capabilities:
        return [], timings_ms if isinstance(timings_ms, dict) else {}

    out = []
    for row in capabilities:
        item = build_capability_contribution_item(row)
        if item:
            out.append(item)
    return out, timings_ms if isinstance(timings_ms, dict) else {}


def get_capability_group_contributions(env):
    del env
    try:
        from odoo.addons.smart_construction_core.services.capability_registry import CAPABILITY_GROUPS
    except Exception:
        return []
    out = []
    for item in CAPABILITY_GROUPS:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("source_module", "smart_construction_core")
        out.append(row)
    return out


def smart_core_list_capabilities_for_user(env, user):
    """Compatibility hook consumed by smart_core capability provider."""
    return get_capability_contributions(env, user)


def smart_core_capability_groups(env):
    """Compatibility hook consumed by smart_core capability provider."""
    return get_capability_group_contributions(env)


def get_create_field_fallback_contributions(env, model_name):
    del env
    return dict(INDUSTRY_CREATE_FIELD_FALLBACKS.get(str(model_name or ""), {}))


def smart_core_create_field_fallbacks(env, model_name):
    """Compatibility hook consumed by smart_core api.data handlers."""
    return get_create_field_fallback_contributions(env, model_name)


def smart_core_form_business_actions(env, model_name, record_id, contract):
    """Return model-level business action semantics for form contracts."""
    del contract
    model = str(model_name or "").strip()
    if model != "payment.request":
        return None
    try:
        record = env[model].browse(int(record_id or 0)).exists()
    except Exception:
        record = None
    if not record:
        return None
    try:
        from odoo.addons.smart_construction_core.handlers.payment_request_available_actions import (
            PaymentRequestAvailableActionsHandler,
        )

        result = PaymentRequestAvailableActionsHandler(env, payload={"id": int(record.id)}).run(
            payload={"id": int(record.id)}
        )
    except Exception:
        return None

    data = result.get("data") if isinstance(result, dict) else {}
    return build_payment_form_business_action_contract(data)


def get_system_init_fact_contributions(env, user, context=None):
    """Return construction system.init facts contribution payload."""
    del context
    try:
        module_facts = {}

        task_rows = _build_task_action_rows(env, user)
        payment_rows = _build_payment_action_rows(env)
        risk_rows = _build_risk_action_rows(env)
        project_rows = _build_project_action_rows(env, user)

        module_facts["workspace_collections"] = {
            "task_items": task_rows,
            "payment_requests": payment_rows,
            "risk_actions": risk_rows,
            "project_actions": project_rows,
        }
        module_facts["workspace_collection_export_keys"] = [
            "task_items",
            "payment_requests",
            "risk_actions",
            "project_actions",
        ]

        module_facts["workspace_business_source"] = {
            "task_items": len(task_rows),
            "payment_requests": len(payment_rows),
            "risk_actions": len(risk_rows),
            "project_actions": len(project_rows),
        }

        role_entries = _build_role_entry_contract_rows(env)
        if role_entries:
            module_facts["role_entries"] = role_entries

        home_blocks = _build_home_block_contract_rows(env)
        if home_blocks:
            module_facts["home_blocks"] = home_blocks

        enterprise_enablement = _build_enterprise_enablement_contract(env, user)
        if enterprise_enablement:
            module_facts["enterprise_enablement"] = enterprise_enablement

        return {
            "module": "smart_construction_core",
            "facts": module_facts,
            "collections": module_facts.get("workspace_collections") or {},
            "meta": {
                "source": "smart_construction_core",
                "status": "active",
            },
        }
    except Exception as exc:
        _logger.warning("[get_system_init_fact_contributions] failed: %s", exc)
        return None


def smart_core_extend_system_init(data, env, user):
    """Compatibility hook: write construction facts only under data['ext_facts']."""
    if not isinstance(data, dict):
        return data

    contribution = get_system_init_fact_contributions(env, user)
    ext_facts = data.get("ext_facts")
    if not isinstance(ext_facts, dict):
        ext_facts = {}
    if isinstance(contribution, dict):
        module_key = str(contribution.get("module") or "smart_construction_core").strip() or "smart_construction_core"
        facts_payload = contribution.get("facts") if isinstance(contribution.get("facts"), dict) else {}
        ext_facts[module_key] = dict(facts_payload)
    data["ext_facts"] = ext_facts
    return apply_system_init_profile_overrides(data, ext_facts)
