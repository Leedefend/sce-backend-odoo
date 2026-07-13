# -*- coding: utf-8 -*-

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
        "landing_scene_candidates": ["projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
    },
    "pm": {
        "landing_scene_candidates": ["portal.dashboard", "projects.ledger", "projects.list", "projects.intake"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_contract_center",
            "smart_construction_core.menu_sc_cost_center",
        ],
        "menu_blocklist_xmlids": ["smart_construction_core.menu_sc_project_manage"],
    },
    "finance": {
        "landing_scene_candidates": ["finance.payment_requests", "projects.ledger", "projects.list"],
        "menu_xmlids": [
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_settlement_center",
            "smart_construction_core.menu_payment_request",
        ],
    },
    "executive": {
        "landing_scene_candidates": ["portal.dashboard", "project.management", "projects.list", "projects.ledger", "projects.intake"],
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

ROLE_PRECEDENCE = ("business_config_admin", "executive", "pm", "finance")

NAV_MENU_SCENE_MAP = {
    "smart_construction_core.menu_sc_project_initiation": "projects.intake",
    "smart_construction_core.menu_sc_project_project": "projects.list",
    "smart_construction_core.menu_sc_project_management_scene": "project.management",
    "smart_construction_core.menu_sc_project_cost_code": "config.project_cost_code",
    "smart_construction_core.menu_sc_root": "projects.list",
    "smart_construction_core.menu_sc_project_dashboard": "projects.dashboard",
    "smart_construction_core.menu_sc_history_todo": "workspace.home",
    "smart_construction_core.menu_sc_operating_metrics_project": "dashboard.company",
    "smart_construction_core.menu_sc_dashboard_cost_cockpit_fact": "cost.control",
    "smart_construction_core.menu_sc_dictionary": "data.dictionary",
    "smart_construction_core.menu_payment_request": "finance.payment_requests",
}

NAV_ACTION_SCENE_MAP = {
    "smart_construction_core.action_project_initiation": "projects.intake",
    "smart_construction_core.action_sc_project_list": "projects.list",
    "smart_construction_core.action_project_dashboard": "projects.dashboard",
    "smart_construction_core.action_project_dictionary": "data.dictionary",
    "smart_construction_core.action_project_cost_code": "config.project_cost_code",
    "smart_construction_core.action_sc_dashboard_cost_cockpit_fact": "cost.control",
    "smart_construction_core.action_payment_request": "finance.payment_requests",
    "smart_construction_core.action_payment_request_my": "finance.payment_requests",
}

NAV_MODEL_VIEW_SCENE_MAP = {
    ("project.project", "list"): "projects.list",
    ("project.project", "form"): "projects.intake",
    ("payment.request", "list"): "finance.payment_requests",
    ("payment.request", "form"): "finance.payment_requests",
}

SERVER_ACTION_WINDOW_MAP = {
    "smart_construction_core.action_exec_structure_entry": "smart_construction_core.action_exec_structure_wbs",
}

FILE_ATTACHMENT_ALLOWED_MODEL_EXACT = {
    "payment.ledger",
    "payment.request",
    "payment.request.line",
    "sc.legacy.fund.confirmation.document",
    "sc.legacy.invoice.tax.fact",
    "sc.legacy.payment.residual.fact",
}
FILE_ATTACHMENT_ALLOWED_MODEL_PREFIXES = ("construction.", "project.", "quota.", "sc.", "tender.")
FILE_ATTACHMENT_ALLOWED_LEGACY_MODEL_PREFIXES = ("sc.legacy.",)
FILE_ATTACHMENT_EXCLUDED_MODEL_PREFIXES = (
    "sc.legacy.",
    "sc.ops.",
    "sc.pack.",
    "sc.scene.",
    "sc.subscription.",
    "sc.usage.",
    "sc.workbench.",
    "ui.form.",
)
FILE_UPLOAD_ALLOWED_MODELS = ["project.project", "project.task", "payment.request"]
FILE_DOWNLOAD_ALLOWED_MODELS = ["project.project", "project.task", "payment.request"]
