# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from odoo.addons.smart_construction_scene import scene_registry

ROLE_SURFACE_OVERRIDES = {
    "business_config_admin": {
        "label": "业务配置管理员",
        "landing_scene_candidates": ["projects.list", "projects.ledger", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_business_config_center",
        ],
    },
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
            "smart_construction_core.menu_sc_material_center",
            "smart_construction_core.menu_sc_construction_management_center",
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
    "business_config_admin": {
        "smart_construction_core.group_sc_cap_business_config_admin",
    },
    "executive": {
        "smart_construction_custom.group_sc_role_executive",
    },
    "pm": {
        "smart_construction_custom.group_sc_role_pm",
        "smart_construction_custom.group_sc_role_project_manager",
        "smart_construction_core.group_sc_role_project_manager",
    },
    "finance": {
        "smart_construction_custom.group_sc_role_finance",
        "smart_construction_custom.group_sc_role_payment_manager",
        "smart_construction_custom.group_sc_role_payment_user",
        "smart_construction_core.group_sc_role_finance_manager",
        "smart_construction_core.group_sc_role_finance_user",
    },
}

ROLE_GROUPS_CAPABILITY_FALLBACK = {
    "pm": {
        "smart_construction_core.group_sc_cap_project_manager",
    },
    "finance": {
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    },
}

ROLE_PRECEDENCE = ("business_config_admin", "executive", "pm", "finance")

NAV_MENU_SCENE_MAP = {
    "smart_construction_core.menu_sc_project_initiation": "projects.intake",
    "smart_construction_core.menu_sc_project_manage": "project.management",
    "smart_construction_core.menu_sc_project_project": "projects.list",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_quick_create": "projects.intake",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "project.dashboard",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
    "smart_construction_core.menu_sc_tier_review_my_payment_request": "payments.approval",
    "smart_construction_core.menu_sc_material_center": "material.center",
    "smart_construction_core.menu_sc_material_catalog": "material.catalog",
    "smart_construction_core.menu_sc_material_purchase_request": "material.procurement",
    "smart_construction_core.menu_sc_material_rfq": "material.rfq",
    "smart_construction_core.menu_sc_material_acceptance": "material.acceptance",
    "smart_construction_core.menu_sc_material_inbound": "material.inbound",
    "smart_construction_core.menu_sc_material_outbound": "material.outbound",
    "smart_construction_core.menu_sc_material_price_library": "material.price_library",
    "smart_construction_core.menu_sc_material_settlement": "material.settlement",
    "smart_construction_core.menu_sc_material_rental_plan": "material.rental",
    "smart_construction_core.menu_sc_material_rental_order": "material.rental_order",
    "smart_construction_core.menu_sc_material_rental_settlement": "material.rental_settlement",
    "smart_construction_core.menu_sc_labor_plan": "labor.management",
    "smart_construction_core.menu_sc_labor_request": "labor.request",
    "smart_construction_core.menu_sc_attendance_checkin": "labor.attendance",
    "smart_construction_core.menu_sc_labor_settlement": "labor.settlement",
    "smart_construction_core.menu_sc_equipment_plan": "equipment.management",
    "smart_construction_core.menu_sc_equipment_request": "equipment.request",
    "smart_construction_core.menu_sc_equipment_usage": "equipment.usage",
    "smart_construction_core.menu_sc_equipment_settlement": "equipment.settlement",
    "smart_construction_core.menu_sc_subcontract_plan": "subcontract.management",
    "smart_construction_core.menu_sc_subcontract_request": "subcontract.request",
    "smart_construction_core.menu_sc_subcontract_register": "subcontract.register",
    "smart_construction_core.menu_sc_subcontract_settlement": "subcontract.settlement",
    "smart_construction_core.menu_sc_construction_management_center": "construction.execution",
    "smart_construction_core.menu_sc_plan": "construction.plan",
    "smart_construction_core.menu_sc_plan_report": "construction.plan_report",
    "smart_construction_core.menu_sc_construction_diary": "construction.diary",
    "smart_construction_core.menu_sc_quality_issue": "quality.center",
    "smart_construction_core.menu_sc_quality_rectification": "quality.rectification",
    "smart_construction_core.menu_sc_quality_recheck": "quality.recheck",
    "smart_construction_core.menu_sc_safety_issue": "safety.center",
    "smart_construction_core.menu_sc_safety_rectification": "safety.rectification",
    "smart_construction_core.menu_sc_safety_recheck": "safety.recheck",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_core.action_project_initiation": "projects.intake",
    "smart_construction_core.action_project_initiation_quick": "projects.intake",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_sc_project_manage": "project.management",
    "smart_construction_core.action_sc_project_my_list": "projects.list",
    "smart_construction_core.action_sc_project_overview": "projects.list",
    "smart_construction_core.action_project_dashboard": "project.dashboard",
    "smart_construction_core.action_project_dictionary": "data.dictionary",
    "smart_construction_core.action_project_cost_code": "config.project_cost_code",
    "smart_construction_core.action_payment_request": "finance.payment_requests",
    "smart_construction_core.action_payment_request_my": "finance.payment_requests",
    "smart_construction_core.action_sc_material_product_template": "material.catalog",
    "smart_construction_core.action_sc_material_purchase_request": "material.procurement",
    "smart_construction_core.action_sc_material_rfq": "material.rfq",
    "smart_construction_core.action_sc_material_acceptance": "material.acceptance",
    "smart_construction_core.action_sc_material_inbound": "material.inbound",
    "smart_construction_core.action_sc_material_outbound": "material.outbound",
    "smart_construction_core.action_sc_material_price_library": "material.price_library",
    "smart_construction_core.action_sc_material_settlement": "material.settlement",
    "smart_construction_core.action_sc_material_rental_plan": "material.rental",
    "smart_construction_core.action_sc_material_rental_order": "material.rental_order",
    "smart_construction_core.action_sc_material_rental_settlement": "material.rental_settlement",
    "smart_construction_core.action_sc_labor_plan": "labor.management",
    "smart_construction_core.action_sc_labor_request": "labor.request",
    "smart_construction_core.action_sc_attendance_checkin": "labor.attendance",
    "smart_construction_core.action_sc_labor_settlement": "labor.settlement",
    "smart_construction_core.action_sc_equipment_plan": "equipment.management",
    "smart_construction_core.action_sc_equipment_request": "equipment.request",
    "smart_construction_core.action_sc_equipment_usage": "equipment.usage",
    "smart_construction_core.action_sc_equipment_settlement": "equipment.settlement",
    "smart_construction_core.action_sc_subcontract_plan": "subcontract.management",
    "smart_construction_core.action_sc_subcontract_request": "subcontract.request",
    "smart_construction_core.action_sc_subcontract_register": "subcontract.register",
    "smart_construction_core.action_sc_subcontract_settlement": "subcontract.settlement",
    "smart_construction_core.action_sc_plan": "construction.plan",
    "smart_construction_core.action_sc_plan_report": "construction.plan_report",
    "smart_construction_core.action_sc_construction_diary": "construction.diary",
    "smart_construction_core.action_sc_quality_issue": "quality.center",
    "smart_construction_core.action_sc_quality_rectification": "quality.rectification",
    "smart_construction_core.action_sc_quality_recheck": "quality.recheck",
    "smart_construction_core.action_sc_safety_issue": "safety.center",
    "smart_construction_core.action_sc_safety_rectification": "safety.rectification",
    "smart_construction_core.action_sc_safety_recheck": "safety.recheck",
}

NAV_MODEL_VIEW_SCENE_MAP = {
    ("project.project", "list"): "projects.list",
    ("project.project", "form"): "projects.intake",
    ("payment.request", "list"): "finance.payment_requests",
    ("payment.request", "form"): "finance.payment_requests",
    ("sc.material.catalog", "list"): "material.catalog",
    ("sc.material.purchase.request", "list"): "material.procurement",
    ("sc.material.rfq", "list"): "material.rfq",
    ("sc.material.acceptance", "list"): "material.acceptance",
    ("sc.material.inbound", "list"): "material.inbound",
    ("sc.material.outbound", "list"): "material.outbound",
    ("sc.material.price", "list"): "material.price_library",
    ("sc.material.settlement", "list"): "material.settlement",
    ("sc.material.rental.plan", "list"): "material.rental",
    ("sc.material.rental.order", "list"): "material.rental_order",
    ("sc.material.rental.settlement", "list"): "material.rental_settlement",
    ("sc.labor.plan", "list"): "labor.management",
    ("sc.labor.request", "list"): "labor.request",
    ("sc.attendance.checkin", "list"): "labor.attendance",
    ("sc.labor.settlement", "list"): "labor.settlement",
    ("sc.equipment.plan", "list"): "equipment.management",
    ("sc.equipment.request", "list"): "equipment.request",
    ("sc.equipment.usage", "list"): "equipment.usage",
    ("sc.equipment.settlement", "list"): "equipment.settlement",
    ("sc.subcontract.plan", "list"): "subcontract.management",
    ("sc.subcontract.request", "list"): "subcontract.request",
    ("sc.subcontract.register", "list"): "subcontract.register",
    ("sc.subcontract.settlement", "list"): "subcontract.settlement",
    ("sc.plan", "list"): "construction.plan",
    ("sc.plan.report", "list"): "construction.plan_report",
    ("sc.construction.diary", "list"): "construction.diary",
    ("sc.quality.issue", "list"): "quality.center",
    ("sc.quality.rectification", "list"): "quality.rectification",
    ("sc.quality.recheck", "list"): "quality.recheck",
    ("sc.safety.issue", "list"): "safety.center",
    ("sc.safety.rectification", "list"): "safety.rectification",
    ("sc.safety.recheck", "list"): "safety.recheck",
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
        "construction.diary",
        "construction.execution",
        "construction.plan",
        "construction.plan_report",
        "data.dictionary",
        "finance.center",
        "finance.operating_metrics",
        "finance.payment_ledger",
        "finance.payment_requests",
        "finance.settlement_orders",
        "finance.treasury_ledger",
        "equipment.management",
        "equipment.request",
        "equipment.settlement",
        "equipment.usage",
        "labor.attendance",
        "labor.management",
        "labor.request",
        "labor.settlement",
        "material.acceptance",
        "material.catalog",
        "material.center",
        "material.inbound",
        "material.outbound",
        "material.price_library",
        "material.procurement",
        "material.rental",
        "material.rental_order",
        "material.rental_settlement",
        "material.rfq",
        "material.settlement",
        "config.project_cost_code",
        "portal.capability_matrix",
        "portal.dashboard",
        "portal.lifecycle",
        "projects.dashboard_showcase",
        "projects.execution",
        "quality.center",
        "quality.recheck",
        "quality.rectification",
        "risk.monitor",
        "safety.center",
        "safety.recheck",
        "safety.rectification",
        "subcontract.management",
        "subcontract.register",
        "subcontract.request",
        "subcontract.settlement",
        "task.center",
    ]
}

SURFACE_POLICY_DEFAULT_NAME = "construction_pm_v1"
SURFACE_POLICY_DEFAULT_FILE = "docs/product/delivery/v1/construction_pm_v1_scene_surface_policy.json"

CRITICAL_SCENE_TARGET_OVERRIDES = {
    "contract.center",
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
    "equipment.management",
    "equipment.request",
    "equipment.usage",
    "equipment.settlement",
    "labor.management",
    "labor.request",
    "labor.attendance",
    "labor.settlement",
    "construction.execution",
    "construction.plan",
    "construction.plan_report",
    "construction.diary",
    "material.center",
    "material.catalog",
    "material.procurement",
    "material.acceptance",
    "material.inbound",
    "material.outbound",
    "material.price_library",
    "material.settlement",
    "material.rental",
    "material.rental_order",
    "material.rental_settlement",
    "material.rfq",
    "quality.center",
    "quality.rectification",
    "quality.recheck",
    "safety.center",
    "safety.rectification",
    "safety.recheck",
    "subcontract.management",
    "subcontract.request",
    "subcontract.register",
    "subcontract.settlement",
}

CRITICAL_SCENE_TARGET_ROUTE_OVERRIDES = {
    "my_work.workspace": "/my-work",
}

_DERIVED_NAV_SCENE_MAP_CACHE: dict[str, dict[str, dict[Any, str]]] = {}


def _scene_cache_key(env) -> str:
    try:
        dbname = str(getattr(getattr(env, "cr", None), "dbname", "") or "").strip()
    except Exception:
        dbname = ""
    return dbname or "__default__"


def _normalize_view_mode(raw: Any) -> str:
    value = str(raw or "").strip().lower()
    if value in {"tree", "list", "kanban"}:
        return "list"
    if value in {"form"}:
        return "form"
    return value


def _derive_nav_scene_maps_from_registry(env) -> dict[str, dict[Any, str]]:
    cache_key = _scene_cache_key(env)
    cached = _DERIVED_NAV_SCENE_MAP_CACHE.get(cache_key)
    if isinstance(cached, dict):
        return cached

    menu_scene_map: dict[str, str] = {}
    action_xmlid_scene_map: dict[str, str] = {}
    model_view_scene_map: dict[tuple[str, str], str] = {}

    try:
        scenes = scene_registry.load_scene_configs(env)
    except Exception:
        scenes = []

    for scene in scenes or []:
        if not isinstance(scene, dict):
            continue
        scene_key = str(scene.get("code") or scene.get("key") or "").strip()
        if not scene_key:
            continue
        target = scene.get("target") if isinstance(scene.get("target"), dict) else {}
        menu_xmlid = str(target.get("menu_xmlid") or "").strip()
        action_xmlid = str(target.get("action_xmlid") or "").strip()
        model = str(target.get("model") or "").strip()
        view_mode = _normalize_view_mode(target.get("view_mode") or target.get("view_type"))

        if menu_xmlid and menu_xmlid not in menu_scene_map:
            menu_scene_map[menu_xmlid] = scene_key
        if action_xmlid and action_xmlid not in action_xmlid_scene_map:
            action_xmlid_scene_map[action_xmlid] = scene_key
        if model and view_mode and (model, view_mode) not in model_view_scene_map:
            model_view_scene_map[(model, view_mode)] = scene_key

    derived = {
        "menu_scene_map": menu_scene_map,
        "action_xmlid_scene_map": action_xmlid_scene_map,
        "model_view_scene_map": model_view_scene_map,
    }
    _DERIVED_NAV_SCENE_MAP_CACHE[cache_key] = derived
    return derived


def get_intent_handler_contributions():
    return []


def smart_core_identity_profile(env):
    del env
    return {
        "role_surface_map": ROLE_SURFACE_OVERRIDES,
        "role_groups_explicit": ROLE_GROUPS_EXPLICIT,
        "role_groups_capability_fallback": ROLE_GROUPS_CAPABILITY_FALLBACK,
        "role_precedence": ROLE_PRECEDENCE,
    }


def smart_core_nav_scene_maps(env):
    derived = _derive_nav_scene_maps_from_registry(env)
    menu_scene_map = dict(derived.get("menu_scene_map") or {})
    action_xmlid_scene_map = dict(derived.get("action_xmlid_scene_map") or {})
    model_view_scene_map = dict(derived.get("model_view_scene_map") or {})
    menu_scene_map.update(NAV_MENU_SCENE_MAP)
    action_xmlid_scene_map.update(NAV_ACTION_SCENE_MAP)
    model_view_scene_map.update(NAV_MODEL_VIEW_SCENE_MAP)
    return {
        "menu_scene_map": menu_scene_map,
        "action_xmlid_scene_map": action_xmlid_scene_map,
        "model_view_scene_map": model_view_scene_map,
    }


def smart_core_load_scene_configs(env, drift=None):
    return scene_registry.load_scene_configs(env, drift=drift)


def smart_core_has_db_scenes(env):
    return scene_registry.has_db_scenes(env)


def smart_core_get_scene_version(env):
    del env
    return scene_registry.get_scene_version()


def smart_core_get_schema_version(env):
    del env
    return scene_registry.get_schema_version()


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
