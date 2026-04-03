# -*- coding: utf-8 -*-
from __future__ import annotations


ROLE_SURFACE_OVERRIDES = {
    "owner": {
        "label": "普通员工",
        "landing_scene_candidates": ["projects.list", "project.initiation", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "label": "项目经理",
        "landing_scene_candidates": [
            "project.management",
            "project.dashboard",
            "projects.intake",
            "projects.list",
            "projects.ledger",
            "my_work.workspace",
        ],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_project_management_scene",
            "smart_construction_core.menu_sc_project_dashboard",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
        "menu_blocklist_xmlids": [],
    },
    "finance": {
        "label": "财务人员",
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "label": "管理层",
        "landing_scene_candidates": [
            "portal.dashboard",
            "project.management",
            "projects.list",
            "projects.ledger",
            "project.initiation",
            "projects.intake",
        ],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_projection_root",
            "smart_construction_core.menu_sc_project_center",
        ],
    },
}

ROLE_GROUPS_EXPLICIT = {
    "executive": {
        "smart_construction_custom.group_sc_role_executive",
    },
    "pm": {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_custom.group_sc_role_project_user",
        "smart_construction_core.group_sc_role_project_manager",
    },
    "finance": {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_custom.group_sc_role_payment_read",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_role_finance_user",
    },
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": {
        "smart_construction_core.group_sc_cap_project_manager",
        "smart_construction_core.group_sc_cap_project_user",
    },
    "finance": {
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    },
}

ROLE_PRECEDENCE = ("executive", "pm", "finance")

NAV_MENU_SCENE_MAP = {
    "smart_construction_demo.menu_sc_project_list_showcase": "projects.list",
    "smart_construction_core.menu_sc_project_initiation": "project.initiation",
    "smart_construction_core.menu_sc_project_project": "projects.ledger",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "project.dashboard",
    "smart_construction_demo.menu_sc_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
    "smart_construction_portal.menu_sc_portal_lifecycle": "portal.lifecycle",
    "smart_construction_portal.menu_sc_portal_capability_matrix": "portal.capability_matrix",
    "smart_construction_portal.menu_sc_portal_dashboard": "portal.dashboard",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_demo.action_sc_project_list_showcase": "projects.list",
    "smart_construction_core.action_project_initiation": "project.initiation",
    "smart_construction_core.action_sc_project_kanban_lifecycle": "projects.ledger",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_project_dashboard": "project.dashboard",
    "smart_construction_demo.action_project_dashboard_showcase": "projects.dashboard_showcase",
    "smart_construction_core.action_project_dictionary": "data.dictionary",
    "smart_construction_core.action_project_cost_code": "config.project_cost_code",
    "smart_construction_core.action_payment_request": "finance.payment_requests",
    "smart_construction_core.action_payment_request_my": "finance.payment_requests",
    "smart_construction_portal.action_sc_portal_lifecycle": "portal.lifecycle",
    "smart_construction_portal.action_sc_portal_capability_matrix": "portal.capability_matrix",
    "smart_construction_portal.action_sc_portal_dashboard": "portal.dashboard",
}

NAV_MODEL_VIEW_SCENE_MAP = {
    ("project.project", "list"): "projects.list",
    ("project.project", "form"): "projects.intake",
    ("payment.request", "list"): "finance.payment_requests",
    ("payment.request", "form"): "finance.payment_requests",
}

SURFACE_NAV_ALLOWLIST = {
    "construction_pm_v1": [
        "project.management",
        "project.dashboard",
        "projects.dashboard",
        "projects.ledger",
        "project.initiation",
        "projects.intake",
        "my_work.workspace",
    ]
}

SURFACE_DEEP_LINK_ALLOWLIST = {
    "construction_pm_v1": [
        "contract.center",
        "cost.budget_alloc",
        "cost.cost_compare",
        "cost.profit_compare",
        "cost.project_boq",
        "cost.project_budget",
        "cost.project_cost_ledger",
        "cost.project_progress",
        "data.dictionary",
        "finance.center",
        "finance.operating_metrics",
        "finance.payment_ledger",
        "finance.payment_requests",
        "finance.settlement_orders",
        "finance.treasury_ledger",
        "config.project_cost_code",
        "risk.monitor",
        "task.center",
    ]
}

SURFACE_POLICY_DEFAULT_NAME = "construction_pm_v1"
SURFACE_POLICY_DEFAULT_FILE = "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"

CRITICAL_SCENE_TARGET_OVERRIDES = {
    "projects.list",
    "projects.detail",
    "projects.intake",
    "projects.ledger",
    "projects.execution",
    "projects.dashboard",
    "project.management",
    "my_work.workspace",
    "portal.dashboard",
    "finance.payment_requests",
}

CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES = {
    "my_work.workspace": "/my-work",
}


def smart_core_register(registry):
    del registry
    return None


def smart_core_identity_profile(env):
    del env
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_nav_scene_maps(env):
    del env
    return {
        "menu_scene_map": NAV_MENU_SCENE_MAP,
        "action_xmlid_scene_map": NAV_ACTION_SCENE_MAP,
        "model_view_scene_map": NAV_MODEL_VIEW_SCENE_MAP,
    }


def smart_core_surface_nav_allowlist(env):
    del env
    return {str(surface): list(codes) for surface, codes in SURFACE_NAV_ALLOWLIST.items()}


def smart_core_surface_deep_link_allowlist(env):
    del env
    return {str(surface): list(codes) for surface, codes in SURFACE_DEEP_LINK_ALLOWLIST.items()}


def smart_core_surface_policy_default_name(env):
    del env
    return SURFACE_POLICY_DEFAULT_NAME


def smart_core_surface_policy_file_default(env):
    del env
    return SURFACE_POLICY_DEFAULT_FILE


def smart_core_critical_scene_target_overrides(env):
    del env
    return list(CRITICAL_SCENE_TARGET_OVERRIDES)


def smart_core_critical_scene_target_route_overrides(env):
    del env
    return dict(CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES)


def smart_core_extend_system_init(data, env, user):
    del user
    try:
        ext_facts = data.get("ext_facts")
        if not isinstance(ext_facts, dict):
            ext_facts = {}
        module_facts = ext_facts.get("smart_construction_scene")
        if not isinstance(module_facts, dict):
            module_facts = {}

        module_facts["role_surface_override_provider"] = {
            "key": "smart_construction_scene",
            "enabled": True,
            "priority": 100,
            "domain_key": "construction",
            "root_xmlids": ["smart_construction_core.menu_sc_root"],
            "scene_codes": ["projects.intake", "projects.list", "projects.ledger", "my_work.workspace", "project.management"],
            "role_surface_overrides": ROLE_SURFACE_OVERRIDES,
        }

        ext_facts["smart_construction_scene"] = module_facts
        data["ext_facts"] = ext_facts
    except Exception:
        return None
    return None
