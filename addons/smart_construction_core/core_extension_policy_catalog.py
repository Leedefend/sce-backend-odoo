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

LEGACY_VISIBLE_BUSINESS_COLUMN_LABELS_BY_MODEL = {
    "project.material.plan": {
        "legacy_visible_01": "单据状态",
        "legacy_visible_02": "单据编号",
        "legacy_visible_03": "单据日期",
        "legacy_visible_04": "到货时间",
        "legacy_visible_05": "采购材料名称",
        "legacy_visible_06": "规格型号",
        "legacy_visible_07": "单位",
        "legacy_visible_08": "数量",
        "legacy_visible_09": "材料别名(设计/清单)",
        "legacy_visible_10": "备注",
        "legacy_visible_11": "附件",
        "legacy_visible_12": "项目名称",
        "legacy_visible_13": "录入人",
        "legacy_visible_14": "录入时间",
        "source_created_by": "录入人",
        "source_created_at": "录入时间",
    },
    "sc.material.inbound": {
        "legacy_visible_01": "单据状态",
        "legacy_visible_02": "入库单号",
        "legacy_visible_03": "单据日期",
        "legacy_visible_04": "供应商名称",
        "legacy_visible_05": "材料名称",
        "legacy_visible_06": "规格型号",
        "legacy_visible_07": "数量",
        "legacy_visible_08": "单价",
        "legacy_visible_09": "税率",
        "legacy_visible_10": "含税金额",
        "legacy_visible_11": "入库总数量",
        "legacy_visible_12": "付款状态",
        "legacy_visible_13": "已付款金额",
        "legacy_visible_14": "未付款金额",
        "legacy_visible_15": "结算状态",
        "legacy_visible_16": "已结算金额",
        "legacy_visible_17": "项目名称",
        "legacy_visible_18": "备注",
        "legacy_visible_19": "附件",
        "legacy_visible_20": "录入人",
        "legacy_visible_21": "录入时间",
        "legacy_visible_22": "采购人",
        "source_created_by": "录入人",
        "source_created_at": "录入时间",
    },
}

MODEL_CODE_MAPPING = {
    "project": "project.project",
    "task": "project.task",
}

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

INDUSTRY_CREATE_FIELD_FALLBACKS = {
    "project.project": {
        "selection_defaults": {
            "privacy_visibility": "followers",
            "rating_status": "stage",
            "last_update_status": "to_define",
            "rating_status_period": "monthly",
        }
    }
}

USER_CONFIRMED_FORMAL_LIST_ACTION_XMLIDS = {
    "smart_construction_core.action_project_material_plan",
    "smart_construction_core.action_sc_labor_usage_ticket",
    "smart_construction_core.action_sc_labor_usage_casual",
    "smart_construction_core.action_sc_equipment_usage_shift_user_confirmed",
    "smart_construction_core.action_sc_material_quote_user_confirmed",
    "smart_construction_core.action_sc_subcontract_request_user_confirmed",
    "smart_construction_core.action_payment_request_user_payment_apply",
    "smart_construction_core.action_sc_payment_execution_partner_payment",
    "smart_construction_core.action_sc_legacy_fuel_card_fact",
    "smart_construction_core.action_sc_legacy_fuel_card_recharge_fact",
    "smart_construction_core.action_sc_expense_claim_deduction_paid",
    "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
}

API_DATA_WRITE_ALLOWLIST = {
    "project.project": ["name", "description", "date_start"],
    "project.task": ["name", "description", "date_deadline", "project_id"],
    "purchase.order.line": ["name", "order_id"],
    "res.partner": ["name", "email", "phone", "sc_supplier_type", "sc_supplier_type_ids"],
}

API_DATA_MUTATION_POLICIES = {
    "sc.legacy.receipt.income.fact": {
        "allowed_ops": ["create", "write"],
        "allowed": False,
        "reason_code": "READONLY_PROJECTION_MUTATION_DENIED",
        "message": "历史事实投影为只读数据，不允许通过业务办理接口创建或修改。",
        "source": "smart_construction_core",
    },
}

DRAFT_DELETE_ALLOWED_STATES = ("cancel", "cancelled", "draft")
