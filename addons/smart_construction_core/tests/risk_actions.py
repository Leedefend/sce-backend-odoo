# -*- coding: utf-8 -*-

# 高风险动作清单（需要显式 groups_id）
RISK_ACTION_XMLIDS = [
    # 原生配置/全局动作
    "base_setup.action_general_configuration",
    "account.action_account_config",
    "stock.action_stock_config_settings",
    "project.project_config_settings_action",
    "purchase.action_purchase_configuration",
    "base.action_module_upgrade",
    # SC 配置/主数据/跨域
    "smart_construction_core.action_project_cost_code",
    "smart_construction_core.action_sc_workflow_def",
    "smart_construction_core.action_project_dashboard",
    "smart_construction_core.action_project_boq_import_wizard",
    "smart_construction_core.action_quota_import_wizard",
    "smart_construction_core.action_project_material_plan",
    "smart_construction_core.action_material_plan_to_rfq_wizard",
    # 财务/合同
    "smart_construction_core.action_payment_request",
    "smart_construction_core.action_sc_tier_review_my_payment_request",
    "smart_construction_core.action_construction_contract",
    # 审批回调 server action
    "smart_construction_core.server_action_material_plan_tier_approved",
    "smart_construction_core.server_action_material_plan_tier_rejected",
    "smart_construction_core.server_action_payment_request_on_approved",
    "smart_construction_core.server_action_payment_request_on_rejected",
]
