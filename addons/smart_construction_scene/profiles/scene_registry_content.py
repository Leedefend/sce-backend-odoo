# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List


def list_scene_entries() -> List[Dict[str, Any]]:
    """Industry scene content entries for registry fallback list.

    Complete migration target: keep industry scene facts in industry layer,
    while registry keeps only platform minimum defaults.
    """
    return [
        {
            "code": "data.dictionary",
            "name": "业务字典",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_dictionary",
                "action_xmlid": "smart_construction_core.action_project_dictionary",
            },
        },
        {
            "code": "config.project_cost_code",
            "name": "成本科目",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_cost_code",
                "action_xmlid": "smart_construction_core.action_project_cost_code",
            },
        },
        {
            "code": "projects.dashboard",
            "name": "项目驾驶舱",
            "target": {
                "route": "/pm/dashboard",
                "menu_xmlid": "smart_construction_core.menu_sc_project_dashboard",
                "action_xmlid": "smart_construction_core.action_project_dashboard",
            },
        },
        {
            "code": "project.dashboard",
            "name": "项目驾驶舱（产品场景）",
            "target": {
                "route": "/s/project.dashboard",
                "menu_xmlid": "smart_construction_core.menu_sc_project_dashboard",
                "action_xmlid": "smart_construction_core.action_project_dashboard",
            },
        },
        {
            "code": "projects.dashboard_showcase",
            "name": "项目驾驶舱样板",
            "tags": ["template"],
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_dashboard",
                "action_xmlid": "smart_construction_core.action_project_dashboard",
                "route": "/s/projects.dashboard_showcase",
            },
        },
        {
            "code": "project.management",
            "name": "项目驾驶舱",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_dashboard",
                "action_xmlid": "smart_construction_core.action_project_dashboard",
                "route": "/s/project.management",
            },
        },
        {
            "code": "projects.intake",
            "name": "项目立项",
            "target": {
                "route": "/s/projects.intake",
                "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
                "action_xmlid": "smart_construction_core.action_project_initiation",
            },
        },
        {
            "code": "project.initiation",
            "name": "项目立项（产品场景）",
            "target": {
                "route": "/s/project.initiation",
            },
        },
        {
            "code": "enterprise.company",
            "name": "企业信息",
            "target": {
                "route": "/s/enterprise.company",
                "menu_xmlid": "smart_enterprise_base.menu_enterprise_company",
                "action_xmlid": "smart_enterprise_base.action_enterprise_company",
                "model": "res.company",
                "view_type": "form",
            },
        },
        {
            "code": "enterprise.department",
            "name": "组织架构",
            "target": {
                "route": "/s/enterprise.department",
                "menu_xmlid": "smart_enterprise_base.menu_enterprise_department",
                "action_xmlid": "smart_enterprise_base.action_enterprise_department",
                "model": "hr.department",
                "view_type": "tree",
            },
        },
        {
            "code": "enterprise.user",
            "name": "用户设置",
            "target": {
                "route": "/s/enterprise.user",
                "menu_xmlid": "smart_enterprise_base.menu_enterprise_user",
                "action_xmlid": "smart_enterprise_base.action_enterprise_user",
                "model": "res.users",
                "view_type": "tree",
            },
        },
        {
            "code": "enterprise.post",
            "name": "岗位管理",
            "target": {
                "route": "/s/enterprise.post",
                "menu_xmlid": "smart_enterprise_base.menu_enterprise_post",
                "action_xmlid": "smart_enterprise_base.action_enterprise_post",
                "model": "sc.enterprise.post",
                "view_type": "tree",
            },
        },
        {
            "code": "projects.list",
            "name": "项目台账",
            "target": {
                "route": "/s/projects.list",
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
        },
        {
            "code": "projects.ledger",
            "name": "项目台账",
            "target": {
                "route": "/s/projects.ledger",
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
        },
        {
            "code": "task.center",
            "name": "任务中心",
            "target": {
                "route": "/s/task.center",
                "action_xmlid": "project.action_view_all_task",
            },
        },
        {
            "code": "task.board",
            "name": "任务看板",
            "target": {
                "route": "/s/task.board",
            },
        },
        {
            "code": "contract.center",
            "name": "合同中心",
            "target": {
                "route": "/s/contract.center",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
            },
        },
        {
            "code": "contracts.workspace",
            "name": "合同管理工作台",
            "target": {
                "route": "/s/contracts.workspace",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
                "action_xmlid": "smart_construction_core.action_construction_contract_my",
            },
        },
        {
            "code": "contracts.monitor",
            "name": "合同履约监控",
            "target": {
                "route": "/s/contracts.monitor",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
            },
        },
        {
            "code": "risk.monitor",
            "name": "风险监控",
            "target": {
                "action_xmlid": "smart_construction_core.action_sc_operating_drill_overpay_risk_pr",
            },
        },
        {
            "code": "risk.center",
            "name": "风险提醒工作台",
            "target": {
                "route": "/s/risk.center",
                "action_xmlid": "smart_construction_core.action_sc_operating_drill_overpay_risk_pr",
            },
        },
        {
            "code": "finance.center",
            "name": "财务中心",
            "target": {
                "route": "/s/finance.center",
                "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
                "action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
            },
        },
        {
            "code": "finance.workspace",
            "name": "资金管理工作台",
            "target": {
                "route": "/s/finance.workspace",
                "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
            },
        },
        {
            "code": "finance.operating_metrics",
            "name": "经营指标看板",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_operating_metrics_project",
                "action_xmlid": "smart_construction_core.action_sc_operating_metrics_project",
            },
        },
        {
            "code": "finance.payment_requests",
            "name": "付款收款申请",
            "target": {
                "route": "/s/finance.payment_requests",
                "menu_xmlid": "smart_construction_core.menu_payment_request",
                "action_xmlid": "smart_construction_core.action_payment_request_my",
            },
        },
        {
            "code": "finance.settlement_orders",
            "name": "结算单",
            "target": {
                "route": "/s/finance.settlement_orders",
                "menu_xmlid": "smart_construction_core.menu_sc_settlement_order",
                "action_xmlid": "smart_construction_core.action_sc_settlement_order",
            },
        },
        {
            "code": "finance.treasury_ledger",
            "name": "资金台账",
            "target": {
                "route": "/s/finance.treasury_ledger",
                "menu_xmlid": "smart_construction_core.menu_sc_treasury_ledger",
                "action_xmlid": "smart_construction_core.action_sc_treasury_ledger",
            },
        },
        {
            "code": "finance.payment_ledger",
            "name": "收付款台账",
            "target": {
                "route": "/s/finance.payment_ledger",
                "menu_xmlid": "smart_construction_core.menu_payment_ledger",
                "action_xmlid": "smart_construction_core.action_payment_ledger",
            },
        },
        {
            "code": "material.center",
            "name": "物资与分包",
            "target": {
                "route": "/s/material.center",
                "menu_xmlid": "smart_construction_core.menu_sc_material_center",
            },
        },
        {
            "code": "material.catalog",
            "name": "材料档案",
            "target": {
                "route": "/s/material.catalog",
                "menu_xmlid": "smart_construction_core.menu_sc_material_catalog",
                "action_xmlid": "smart_construction_core.action_sc_material_product_template",
            },
        },
        {
            "code": "material.procurement",
            "name": "采购协同",
            "target": {
                "route": "/s/material.procurement",
                "menu_xmlid": "smart_construction_core.menu_sc_material_purchase_request",
                "action_xmlid": "smart_construction_core.action_sc_material_purchase_request",
            },
        },
        {
            "code": "material.rfq",
            "name": "询比价",
            "target": {
                "route": "/s/material.rfq",
                "menu_xmlid": "smart_construction_core.menu_sc_material_rfq",
                "action_xmlid": "smart_construction_core.action_sc_material_rfq",
            },
        },
        {
            "code": "material.acceptance",
            "name": "材料进场验收",
            "target": {
                "route": "/s/material.acceptance",
                "menu_xmlid": "smart_construction_core.menu_sc_material_acceptance",
                "action_xmlid": "smart_construction_core.action_sc_material_acceptance",
            },
        },
        {
            "code": "material.inbound",
            "name": "入库单",
            "target": {
                "route": "/s/material.inbound",
                "menu_xmlid": "smart_construction_core.menu_sc_material_inbound",
                "action_xmlid": "smart_construction_core.action_sc_material_inbound",
            },
        },
        {
            "code": "material.outbound",
            "name": "出库单",
            "target": {
                "route": "/s/material.outbound",
                "menu_xmlid": "smart_construction_core.menu_sc_material_outbound",
                "action_xmlid": "smart_construction_core.action_sc_material_outbound",
            },
        },
        {
            "code": "material.price_library",
            "name": "材料价格库",
            "target": {
                "route": "/s/material.price_library",
                "menu_xmlid": "smart_construction_core.menu_sc_material_price_library",
                "action_xmlid": "smart_construction_core.action_sc_material_price_library",
            },
        },
        {
            "code": "material.settlement",
            "name": "材料结算",
            "target": {
                "route": "/s/material.settlement",
                "menu_xmlid": "smart_construction_core.menu_sc_material_settlement",
                "action_xmlid": "smart_construction_core.action_sc_material_settlement",
            },
        },
        {
            "code": "material.rental",
            "name": "周转材料租赁",
            "target": {
                "route": "/s/material.rental",
                "menu_xmlid": "smart_construction_core.menu_sc_material_rental_plan",
                "action_xmlid": "smart_construction_core.action_sc_material_rental_plan",
            },
        },
        {
            "code": "material.rental_order",
            "name": "租赁单",
            "target": {
                "route": "/s/material.rental_order",
                "menu_xmlid": "smart_construction_core.menu_sc_material_rental_order",
                "action_xmlid": "smart_construction_core.action_sc_material_rental_order",
            },
        },
        {
            "code": "material.rental_settlement",
            "name": "租赁结算",
            "target": {
                "route": "/s/material.rental_settlement",
                "menu_xmlid": "smart_construction_core.menu_sc_material_rental_settlement",
                "action_xmlid": "smart_construction_core.action_sc_material_rental_settlement",
            },
        },
        {
            "code": "labor.management",
            "name": "劳务管理",
            "target": {
                "route": "/s/labor.management",
                "menu_xmlid": "smart_construction_core.menu_sc_labor_plan",
                "action_xmlid": "smart_construction_core.action_sc_labor_plan",
            },
        },
        {
            "code": "labor.request",
            "name": "劳务申请",
            "target": {
                "route": "/s/labor.request",
                "menu_xmlid": "smart_construction_core.menu_sc_labor_request",
                "action_xmlid": "smart_construction_core.action_sc_labor_request",
            },
        },
        {
            "code": "labor.attendance",
            "name": "考勤记录",
            "target": {
                "route": "/s/labor.attendance",
                "menu_xmlid": "smart_construction_core.menu_sc_attendance_checkin",
                "action_xmlid": "smart_construction_core.action_sc_attendance_checkin",
            },
        },
        {
            "code": "labor.settlement",
            "name": "劳务结算",
            "target": {
                "route": "/s/labor.settlement",
                "menu_xmlid": "smart_construction_core.menu_sc_labor_settlement",
                "action_xmlid": "smart_construction_core.action_sc_labor_settlement",
            },
        },
        {
            "code": "equipment.management",
            "name": "机械设备",
            "target": {
                "route": "/s/equipment.management",
                "menu_xmlid": "smart_construction_core.menu_sc_equipment_plan",
                "action_xmlid": "smart_construction_core.action_sc_equipment_plan",
            },
        },
        {
            "code": "equipment.request",
            "name": "设备申请",
            "target": {
                "route": "/s/equipment.request",
                "menu_xmlid": "smart_construction_core.menu_sc_equipment_request",
                "action_xmlid": "smart_construction_core.action_sc_equipment_request",
            },
        },
        {
            "code": "equipment.usage",
            "name": "设备使用登记",
            "target": {
                "route": "/s/equipment.usage",
                "menu_xmlid": "smart_construction_core.menu_sc_equipment_usage",
                "action_xmlid": "smart_construction_core.action_sc_equipment_usage",
            },
        },
        {
            "code": "equipment.settlement",
            "name": "设备结算",
            "target": {
                "route": "/s/equipment.settlement",
                "menu_xmlid": "smart_construction_core.menu_sc_equipment_settlement",
                "action_xmlid": "smart_construction_core.action_sc_equipment_settlement",
            },
        },
        {
            "code": "subcontract.management",
            "name": "专业分包",
            "target": {
                "route": "/s/subcontract.management",
                "menu_xmlid": "smart_construction_core.menu_sc_subcontract_plan",
                "action_xmlid": "smart_construction_core.action_sc_subcontract_plan",
            },
        },
        {
            "code": "subcontract.request",
            "name": "分包申请",
            "target": {
                "route": "/s/subcontract.request",
                "menu_xmlid": "smart_construction_core.menu_sc_subcontract_request",
                "action_xmlid": "smart_construction_core.action_sc_subcontract_request",
            },
        },
        {
            "code": "subcontract.register",
            "name": "分包登记",
            "target": {
                "route": "/s/subcontract.register",
                "menu_xmlid": "smart_construction_core.menu_sc_subcontract_register",
                "action_xmlid": "smart_construction_core.action_sc_subcontract_register",
            },
        },
        {
            "code": "subcontract.settlement",
            "name": "分包结算",
            "target": {
                "route": "/s/subcontract.settlement",
                "menu_xmlid": "smart_construction_core.menu_sc_subcontract_settlement",
                "action_xmlid": "smart_construction_core.action_sc_subcontract_settlement",
            },
        },
        {
            "code": "cost.cost_compare",
            "name": "成本中心",
            "target": {
                "route": "/s/cost.cost_compare",
                "menu_xmlid": "smart_construction_core.menu_sc_cost_center",
                "action_xmlid": "smart_construction_core.action_project_cost_compare",
            },
        },
        {
            "code": "cost.project_budget",
            "name": "预算管理",
            "target": {
                "route": "/s/cost.project_budget",
            },
        },
        {
            "code": "cost.project_boq",
            "name": "工程量清单",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_boq_root",
                "action_xmlid": "smart_construction_core.action_project_boq_line",
            },
        },
        {
            "code": "cost.budget_alloc",
            "name": "预算分配",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_budget_alloc",
                "action_xmlid": "smart_construction_core.action_project_budget_cost_alloc",
            },
        },
        {
            "code": "cost.analysis",
            "name": "成本控制工作台",
            "target": {
                "route": "/s/cost.analysis",
                "menu_xmlid": "smart_construction_core.menu_sc_project_cost_ledger",
                "action_xmlid": "smart_construction_core.action_project_cost_ledger",
            },
        },
        {
            "code": "cost.control",
            "name": "成本驾驶舱",
            "target": {
                "route": "/s/cost.control",
                "menu_xmlid": "smart_construction_core.menu_sc_dashboard_cost_cockpit_fact",
                "action_xmlid": "smart_construction_core.action_sc_dashboard_cost_cockpit_fact",
            },
        },
        {
            "code": "cost.project_progress",
            "name": "进度填报",
            "target": {
                "route": "/s/cost.project_progress",
                "menu_xmlid": "smart_construction_core.menu_sc_project_progress",
                "action_xmlid": "smart_construction_core.action_project_progress_entry",
            },
        },
        {
            "code": "cost.project_cost_ledger",
            "name": "成本台账",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_cost_ledger",
                "action_xmlid": "smart_construction_core.action_project_cost_ledger",
            },
        },
        {
            "code": "cost.profit_compare",
            "name": "盈亏对比",
            "target": {
                "route": "/s/cost.profit_compare",
                "menu_xmlid": "smart_construction_core.menu_sc_profit_reports",
                "action_xmlid": "smart_construction_core.action_project_profit_compare",
            },
        },
        {
            "code": "construction.execution",
            "name": "施工管理",
            "target": {
                "route": "/s/construction.execution",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_management_center",
            },
        },
        {
            "code": "construction.plan",
            "name": "计划管理",
            "target": {
                "route": "/s/construction.plan",
                "menu_xmlid": "smart_construction_core.menu_sc_plan",
                "action_xmlid": "smart_construction_core.action_sc_plan",
            },
        },
        {
            "code": "construction.plan_report",
            "name": "计划汇报",
            "target": {
                "route": "/s/construction.plan_report",
                "menu_xmlid": "smart_construction_core.menu_sc_plan_report",
                "action_xmlid": "smart_construction_core.action_sc_plan_report",
            },
        },
        {
            "code": "construction.diary",
            "name": "施工日志",
            "target": {
                "route": "/s/construction.diary",
                "menu_xmlid": "smart_construction_core.menu_sc_construction_diary",
                "action_xmlid": "smart_construction_core.action_sc_construction_diary",
            },
        },
        {
            "code": "quality.center",
            "name": "质量检查",
            "target": {
                "route": "/s/quality.center",
                "menu_xmlid": "smart_construction_core.menu_sc_quality_issue",
                "action_xmlid": "smart_construction_core.action_sc_quality_issue",
            },
        },
        {
            "code": "quality.rectification",
            "name": "质量整改",
            "target": {
                "route": "/s/quality.rectification",
                "menu_xmlid": "smart_construction_core.menu_sc_quality_rectification",
                "action_xmlid": "smart_construction_core.action_sc_quality_rectification",
            },
        },
        {
            "code": "quality.recheck",
            "name": "质量复验",
            "target": {
                "route": "/s/quality.recheck",
                "menu_xmlid": "smart_construction_core.menu_sc_quality_recheck",
                "action_xmlid": "smart_construction_core.action_sc_quality_recheck",
            },
        },
        {
            "code": "safety.center",
            "name": "安全检查",
            "target": {
                "route": "/s/safety.center",
                "menu_xmlid": "smart_construction_core.menu_sc_safety_issue",
                "action_xmlid": "smart_construction_core.action_sc_safety_issue",
            },
        },
        {
            "code": "safety.rectification",
            "name": "安全整改",
            "target": {
                "route": "/s/safety.rectification",
                "menu_xmlid": "smart_construction_core.menu_sc_safety_rectification",
                "action_xmlid": "smart_construction_core.action_sc_safety_rectification",
            },
        },
        {
            "code": "safety.recheck",
            "name": "安全复验",
            "target": {
                "route": "/s/safety.recheck",
                "menu_xmlid": "smart_construction_core.menu_sc_safety_recheck",
                "action_xmlid": "smart_construction_core.action_sc_safety_recheck",
            },
        },
        {
            "code": "portal.lifecycle",
            "name": "生命周期驾驶舱",
            "target": {"route": "/s/projects.dashboard"},
        },
        {
            "code": "portal.capability_matrix",
            "name": "能力矩阵",
            "target": {"route": "/s/portal.capability_matrix"},
        },
        {
            "code": "portal.dashboard",
            "name": "角色首页",
            "target": {"route": "/"},
        },
        {
            "code": "payments.approval",
            "name": "收付款审批中心",
            "target": {
                "route": "/s/payments.approval",
                "menu_xmlid": "smart_construction_core.menu_sc_tier_review_my_payment_request",
                "action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
            },
        },
        {
            "code": "my_work.workspace",
            "name": "我的工作",
            "target": {"route": "/my-work"},
        },
        {
            "code": "projects.detail",
            "name": "项目详情",
            "target": {
                "route": "/s/projects.detail",
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
            },
        },
        {
            "code": "projects.execution",
            "name": "项目执行中心",
            "target": {
                "route": "/s/projects.execution",
                "menu_xmlid": "smart_construction_core.menu_sc_root",
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
        },
        {
            "code": "portfolio.center",
            "name": "项目组合中心",
            "target": {"route": "/s/portfolio.center"},
        },
        {
            "code": "portfolio.monitor",
            "name": "项目组合监控",
            "target": {"route": "/s/portfolio.monitor"},
        },
        {
            "code": "contracts.execution",
            "name": "合同执行跟踪",
            "target": {"route": "/s/contracts.execution"},
        },
        {
            "code": "cost.forecast",
            "name": "成本预测",
            "target": {"route": "/s/cost.forecast"},
        },
        {
            "code": "cost.warning.center",
            "name": "成本预警中心",
            "target": {"route": "/s/cost.warning.center"},
        },
        {
            "code": "payments.collection.center",
            "name": "收款管理中心",
            "target": {"route": "/s/payments.collection.center"},
        },
        {
            "code": "payments.risk.control",
            "name": "付款风险控制",
            "target": {"route": "/s/payments.risk.control"},
        },
        {
            "code": "resource.center",
            "name": "资源调配中心",
            "target": {"route": "/s/resource.center"},
        },
        {
            "code": "delivery.command",
            "name": "交付指挥台",
            "target": {"route": "/s/delivery.command"},
        },
        {
            "code": "operation.overview",
            "name": "经营总览",
            "target": {"route": "/s/operation.overview"},
        },
        {
            "code": "workspace.home",
            "name": "角色首页",
            "target": {
                "route": "/s/workspace.home",
                "menu_xmlid": "smart_construction_core.menu_sc_history_todo",
                "intent": "workspace.home.enter",
            },
        },
        {
            "code": "dashboard.company",
            "name": "公司驾驶舱",
            "target": {
                "route": "/s/dashboard.company",
                "menu_xmlid": "smart_construction_core.menu_sc_operating_metrics_project",
                "intent": "dashboard.company.enter",
            },
        },
    ]
