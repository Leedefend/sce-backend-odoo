# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

def business_config_admin_group_xmlids():
    return [
        "smart_construction_core.group_sc_cap_business_config_admin",
        "smart_construction_core.group_sc_role_business_admin",
    ]

def business_config_form_settings_refs():
    return {
        "action_xmlid": "smart_construction_core.action_ui_form_field_policy_business_config",
        "menu_xmlid": "smart_construction_core.menu_ui_form_field_policy_business_config",
    }

def business_config_approval_policy_refs():
    return {
        "action_xmlid": "smart_construction_core.action_sc_approval_policy",
        "menu_xmlid": "smart_construction_core.menu_sc_approval_policy",
    }

def native_config_root_menu_xmlid():
    return "smart_construction_core.menu_sc_business_config_center"

def native_config_delivery_excluded_menu_xmlids():
    return [
        "smart_construction_core.menu_project_quota_root",
        "smart_construction_core.menu_project_quota_center",
        "smart_construction_core.menu_project_quota_subitem",
        "smart_construction_core.menu_project_quota_tree",
        "smart_construction_core.menu_sc_dictionary_root",
        "smart_construction_core.menu_sc_dictionary_all",
        "smart_construction_core.menu_sc_dictionary_discipline",
        "smart_construction_core.menu_sc_dictionary_chapter",
        "smart_construction_core.menu_sc_dictionary_quota_item",
        "smart_construction_core.menu_sc_dictionary_sub_item",
        "smart_construction_core.menu_quota_import_wizard",
    ]

def lowcode_system_config_menu_xmlids():
    return [
        "smart_construction_core.menu_sc_business_config_center",
        "smart_construction_core.menu_sc_business_base_config_group",
        "smart_construction_core.menu_sc_lowcode_system_config_group",
        "smart_construction_core.menu_sc_business_category",
        "smart_construction_core.menu_sc_dictionary",
        "smart_construction_core.menu_sc_organization_department",
        "smart_construction_core.menu_sc_approval_scope",
        "smart_construction_core.menu_sc_approval_policy",
        "smart_construction_core.menu_sc_project_stage_requirement_items",
        "smart_construction_core.menu_sc_project_cost_code",
        "smart_construction_core.menu_sc_company_document_archive",
        "smart_construction_core.menu_sc_business_config_workbench",
        "smart_construction_core.menu_ui_menu_config_policy_business_config",
        "smart_construction_core.menu_ui_form_field_policy_business_config",
        "smart_construction_core.menu_ui_form_custom_field_wizard_business_config",
    ]

def lowcode_config_recovery_parent_menu_xmlids():
    return [
        "smart_construction_core.menu_sc_business_config_center",
    ]

def business_root_menu_xmlid():
    return "smart_construction_core.menu_sc_root"

def menu_delivery_token_policy():
    business_tokens = [
        "定额库",
        "成本科目",
        "阶段资料要求",
        "项目阶段资料要求",
    ]
    user_tokens = [
        "智能施工 2.0",
        "项目管理",
        "合同管理",
        "合同中心",
        "项目合同",
        "收入合同",
        "支出合同",
        "一般合同",
        "施工管理",
        "计划管理",
        "计划汇报",
        "成本管理",
        "成本报表",
        "智慧大屏",
        "大屏",
        "驾驶舱",
        "财税报表",
        "物资与分包",
        "物资管理",
        "材料管理",
        "材料",
        "采购",
        "采购订单",
        "劳务",
        "机械",
        "设备",
        "专业分包",
        "分包",
        "考勤",
        "看板中心",
        "财务账款",
        "结算中心",
        "执行结构",
        "项目立项",
        "项目台账",
        "项目驾驶舱",
        "投标",
        "报名",
        "开标",
        "中标",
        "保证金",
        "自筹",
        "付款还",
        "资金借还",
        "借款",
        "还款",
        "费用中心",
        "费用",
        "报销",
        "收支",
        "统计表",
        "经营情况表",
        "收入",
        "公司财务支出",
        "项目资金",
        "承包人",
        "项目款",
        "公司款",
        "发票税务",
        "发票",
        "开票",
        "税务",
        "付款",
        "实付",
        "付款登记",
        "支付",
        "往来单位付款",
        "扣款",
        "实缴",
        "资金账户",
        "账户间资金往来",
        "收款",
        "到款",
        "资金日报",
        "工程资料",
        "客户",
        "供应商",
        "人事行政",
        "请假",
        "休假",
        "印章",
        "资料证照",
        "证照",
        "借阅",
        "业务配置",
        "配置中心",
        "组织架构",
        "历史用户",
        "历史用户权限",
        "用户信息",
        "用户信息与权限",
        "历史角色",
        "项目授权范围",
        "系统配置",
        "用户验收",
        "直营项目系统菜单",
    ]
    admin_tokens = [
        "执行与生产",
        "成本与资金",
    ]
    return {
        "always_hidden_technical_tokens": ["项目管理（后台）"],
        "business_config_tokens": business_tokens,
        "user_allowed_path_tokens": user_tokens,
        "admin_allowed_path_tokens": [*user_tokens, *admin_tokens],
        "hide_exact_labels": [
            "快速创建项目",
            "项目列表（演示）",
        ],
        "rename_labels": {
            "项目台账（试点）": "项目台账",
            "开票申请": "销项开票申请",
            "开票登记": "销项发票登记",
            "进项上报": "进项税额上报",
        },
    }

def business_nav_group_display_order():
    return {
        "基础资料": 5,
        "项目中心": 10,
        "投标管理类单据": 20,
        "合同中心": 30,
        "施工管理": 40,
        "物资与分包": 50,
        "财务中心": 60,
        "人事行政": 70,
        "资料证照": 80,
        "配置中心": 990,
        "配置": 990,
        "系统配置": 990,
    }

def product_policy_catalog_source(source_env=None):
    del source_env
    return {
        "module": "smart_construction_core",
        "xmlid_prefix": "smart_construction_core.",
        "root_label": "智慧施工管理平台",
    }

def product_policy_catalog_base_keys():
    return ["construction"]

def default_product_policy_specs():
    return [
        ("construction.standard", "施工管理标准版"),
        ("construction.preview", "施工管理预览版"),
    ]

def product_policy_catalog_label(identity: dict[str, Any] | None):
    edition_key = str((identity or {}).get("edition_key") or "").strip()
    return "施工管理预览版" if edition_key == "preview" else "施工管理标准版"

def platform_legacy_ownership_module():
    return "smart_construction_core"

def default_release_snapshot_role_code():
    return "pm"

def industry_extension_module_names():
    return [
        "smart_construction_core",
        "smart_construction_scene",
        "smart_construction_portal",
    ]

def app_shell_contract():
    return {
        "taxonomy": {
            "dashboard": {"label": "经营驾驶舱", "category": "management", "sequence": 10, "primary_scene": "dashboard.company"},
            "projects": {"label": "项目管理", "category": "business", "sequence": 20, "primary_scene": "projects.list"},
            "contracts": {"label": "合同管理", "category": "business", "sequence": 30, "primary_scene": "contracts.workspace"},
            "cost": {"label": "成本管理", "category": "business", "sequence": 40, "primary_scene": "cost.cost_compare"},
            "finance": {"label": "资金财务", "category": "business", "sequence": 50, "primary_scene": "finance.payment_requests"},
            "payments": {"label": "收支办理", "category": "business", "sequence": 60, "primary_scene": "payments.approval"},
            "operation": {"label": "运营管理", "category": "business", "sequence": 80, "primary_scene": "operation.overview"},
            "portfolio": {"label": "项目组合", "category": "management", "sequence": 90, "primary_scene": "portfolio.center"},
            "risk": {"label": "风险管理", "category": "governance", "sequence": 100, "primary_scene": "risk.center"},
            "quality": {"label": "质量管理", "category": "business", "sequence": 110, "primary_scene": "quality.center"},
            "safety": {"label": "安全管理", "category": "business", "sequence": 120, "primary_scene": "safety.center"},
            "resource": {"label": "资源管理", "category": "business", "sequence": 130, "primary_scene": "resource.center"},
            "task": {"label": "任务协同", "category": "productivity", "sequence": 140, "primary_scene": "task.center"},
        },
        "aliases": {
            "project": "projects",
            "contract": "contracts",
            "payment": "payments",
        },
    }

def scene_entry_orchestrator_specs():
    common_project_summary = ("project_code", "manager_name", "stage_name")
    return {
        "ProjectDashboardSceneOrchestrator": {
            "scene_key": "project.management",
            "scene_label": "项目驾驶舱",
            "state_fallback_text": "后端未提供项目驾驶舱状态摘要",
            "title_empty": "项目驾驶舱",
            "title_template": "项目驾驶舱：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_dashboard_progress",
            "suggested_action_reason_code": "PROJECT_DASHBOARD_READY",
            "block_fetch_intent": "project.dashboard.block.fetch",
            "block_alias_map": {"risk": "risks"},
            "first_action_block_keys": ["progress"],
            "entry_summary_keys": (
                "project_code",
                "manager_name",
                "partner_name",
                "stage_name",
                "lifecycle_state",
                "milestone",
                "health_state",
                "progress_percent",
                "cost_total",
                "payment_total",
                "status",
            ),
            "entry_blocks": (
                ("progress", "项目进度", "deferred"),
                ("risks", "风险提醒", "deferred"),
                ("next_actions", "下一步动作", "deferred"),
            ),
        },
        "ProjectExecutionSceneOrchestrator": {
            "scene_key": "project.execution",
            "scene_label": "项目执行",
            "state_fallback_text": "后端未提供项目执行状态摘要",
            "title_empty": "项目执行",
            "title_template": "项目执行：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_execution_next_actions",
            "suggested_action_reason_code": "PROJECT_EXECUTION_READY",
            "block_fetch_intent": "project.execution.block.fetch",
            "first_action_block_keys": ["next_actions", "execution_tasks"],
            "entry_summary_keys": common_project_summary + ("date_start", "date_end"),
            "entry_blocks": (
                ("execution_tasks", "执行任务", "deferred"),
                ("readiness_precheck", "上线前检查", "deferred"),
                ("next_actions", "下一步动作", "deferred"),
            ),
        },
        "ProjectPlanBootstrapSceneOrchestrator": {
            "scene_key": "project.plan_bootstrap",
            "scene_label": "计划准备",
            "state_fallback_text": "后端未提供计划准备状态摘要",
            "title_empty": "计划编排",
            "title_template": "计划准备：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_plan_next_actions",
            "suggested_action_reason_code": "PROJECT_PLAN_BOOTSTRAP_READY",
            "block_fetch_intent": "project.plan_bootstrap.block.fetch",
            "first_action_block_keys": ["next_actions", "plan_summary_detail"],
            "entry_summary_keys": common_project_summary + ("date_start", "date_end"),
            "entry_blocks": (
                ("plan_summary_detail", "计划摘要", "deferred"),
                ("plan_tasks", "计划任务", "deferred"),
                ("next_actions", "计划下一步", "deferred"),
            ),
        },
        "PaymentSliceContractOrchestrator": {
            "scene_key": "payment",
            "scene_label": "支付记录",
            "state_fallback_text": "后端未提供支付记录状态摘要",
            "title_empty": "支付记录",
            "title_template": "支付记录：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_payment_entry",
            "suggested_action_reason_code": "PAYMENT_SLICE_PREPARED_READY",
            "block_fetch_intent": "payment.block.fetch",
            "first_action_block_keys": ["payment_entry", "payment_list"],
            "entry_summary_keys": common_project_summary + ("payment_record_count", "payment_total_amount"),
            "entry_blocks": (
                ("payment_entry", "支付录入", "deferred"),
                ("payment_list", "支付记录", "deferred"),
                ("payment_summary", "支付汇总", "deferred"),
                ("next_actions", "支付下一步", "deferred"),
            ),
        },
        "SettlementSliceContractOrchestrator": {
            "scene_key": "settlement",
            "scene_label": "结算结果",
            "state_fallback_text": "后端未提供结算结果状态摘要",
            "title_empty": "结算结果",
            "title_template": "结算结果：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_settlement_summary",
            "suggested_action_reason_code": "SETTLEMENT_SLICE_PREPARED_READY",
            "block_fetch_intent": "settlement.block.fetch",
            "entry_summary_keys": common_project_summary + ("total_cost", "total_payment", "delta"),
            "entry_blocks": (
                ("settlement_summary", "结算结果", "deferred"),
                ("next_actions", "结算下一步", "deferred"),
            ),
        },
        "CostTrackingContractOrchestrator": {
            "scene_key": "cost.tracking",
            "scene_label": "成本记录",
            "state_fallback_text": "后端未提供成本记录状态摘要",
            "title_empty": "成本记录",
            "title_template": "成本记录：{name}",
            "title_record_name_fallback": "项目",
            "suggested_action_key": "load_cost_entry",
            "suggested_action_reason_code": "COST_SLICE_PREPARED_READY",
            "block_fetch_intent": "cost.tracking.block.fetch",
            "first_action_block_keys": ["cost_entry", "cost_list"],
            "entry_summary_keys": common_project_summary + ("cost_record_count", "cost_total_amount"),
            "entry_blocks": (
                ("cost_entry", "成本录入", "deferred"),
                ("cost_list", "成本记录", "deferred"),
                ("cost_summary", "成本汇总", "deferred"),
                ("next_actions", "成本下一步", "deferred"),
            ),
        },
    }

def user_data_acceptance_nav_contract():
    return {
        "formal_group_child_labels": ["客户", "供应商"],
        "formal_group_labels": ["配置中心"],
        "old_acceptance_group_labels": ["用户核对菜单", "旧业务数据核对"],
        "direct_acceptance_group_labels": ["直营项目数据核对", "直营项目系统菜单"],
        "joint_acceptance_group_labels": ["联营项目数据核对", "联营项目系统菜单"],
        "direct_acceptance_child_tokens": ["直营"],
        "joint_acceptance_child_tokens": ["联营"],
        "acceptance_root_labels": ["用户验收", "直营项目数据核对"],
        "acceptance_root_group_label": "用户数据验收",
        "direct_acceptance_group_label": "直营项目数据核对",
        "joint_acceptance_group_label": "联营项目数据核对",
        "source_menu_group_labels_to_hide": ["用户核对菜单"],
        "acceptance_surface_menu_ids": [727, 729, 735, 770],
        "acceptance_surface_action_ids": [899],
        "acceptance_surface_tokens": [
            "用户验收",
            "用户数据验收",
            "用户核对菜单",
            "menu_scbsly_acceptance_",
            "menu_scbs55_user_acceptance_",
            "menu_scbsly_direct_project_acceptance_root",
            "menu_sc_legacy_engineering_progress_receipt",
        ],
        "old_acceptance_menu_xmlids": [
            "smart_construction_core.menu_scbs55_user_acceptance_445_工程进度收款",
        ],
        "joint_acceptance_menu_xmlids": [
            "smart_construction_core.menu_scbsly_joint_acceptance_self_funding_advance_income",
            "smart_construction_core.menu_scbsly_joint_acceptance_self_funding_advance_refund",
            "smart_construction_core.menu_scbsly_joint_acceptance_supplier_contract",
            "smart_construction_core.menu_scbsly_joint_acceptance_labor_contract",
            "smart_construction_core.menu_scbsly_joint_acceptance_rental_contract",
        ],
        "contract_product_menu_xmlids": [
            "smart_construction_core.menu_sc_contract_income",
            "smart_construction_core.menu_sc_project_income_contract",
            "smart_construction_core.menu_sc_income_contract_execution",
            "smart_construction_core.menu_sc_contract_event",
            "smart_construction_core.menu_sc_general_contract",
            "smart_construction_core.menu_sc_contract_expense",
            "smart_construction_core.menu_sc_expense_contract_execution",
        ],
        "settlement_product_menu_xmlids": [
            "smart_construction_core.menu_sc_settlement_order",
            "smart_construction_core.menu_sc_settlement_adjustment",
            "smart_construction_core.menu_sc_income_contract_settlement",
            "smart_construction_core.menu_sc_expense_contract_settlement",
            "smart_construction_core.menu_sc_material_settlement",
            "smart_construction_core.menu_sc_labor_settlement",
            "smart_construction_core.menu_sc_equipment_settlement",
            "smart_construction_core.menu_sc_material_rental_settlement",
            "smart_construction_core.menu_sc_subcontract_settlement",
        ],
    }
