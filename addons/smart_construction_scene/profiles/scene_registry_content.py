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
            "name": "项目驾驶舱（演示）",
            "is_test": True,
            "tags": ["internal"],
            "target": {
                "menu_xmlid": "smart_construction_demo.menu_sc_project_dashboard_showcase",
                "action_xmlid": "smart_construction_demo.action_project_dashboard_showcase",
            },
        },
        {
            "code": "project.management",
            "name": "项目驾驶舱",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_management_scene",
                "route": "/s/project.management",
            },
        },
        {
            "code": "projects.intake",
            "name": "项目立项",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
                "action_xmlid": "smart_construction_core.action_project_initiation",
            },
        },
        {
            "code": "project.initiation",
            "name": "项目立项（产品场景）",
            "target": {
                "route": "/s/project.initiation",
                "menu_xmlid": "smart_construction_core.menu_sc_project_initiation",
                "action_xmlid": "smart_construction_core.action_project_initiation",
            },
        },
        {
            "code": "projects.list",
            "name": "项目列表",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_root",
                "action_xmlid": "smart_construction_core.action_sc_project_list",
            },
        },
        {
            "code": "projects.ledger",
            "name": "项目台账",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
            },
        },
        {
            "code": "task.center",
            "name": "任务中心",
            "target": {
                "action_xmlid": "project.action_view_all_task",
            },
        },
        {
            "code": "contract.center",
            "name": "合同中心",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
                "action_xmlid": "smart_construction_core.action_construction_contract_my",
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
                "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
                "action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
            },
        },
        {
            "code": "finance.workspace",
            "name": "资金管理工作台",
            "target": {
                "route": "/s/finance.workspace",
                "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
                "action_xmlid": "smart_construction_core.action_sc_tier_review_my_payment_request",
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
                "menu_xmlid": "smart_construction_core.menu_payment_request",
                "action_xmlid": "smart_construction_core.action_payment_request",
            },
        },
        {
            "code": "finance.settlement_orders",
            "name": "结算单",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_settlement_order",
                "action_xmlid": "smart_construction_core.action_sc_settlement_order",
            },
        },
        {
            "code": "finance.treasury_ledger",
            "name": "资金台账",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_treasury_ledger",
                "action_xmlid": "smart_construction_core.action_sc_treasury_ledger",
            },
        },
        {
            "code": "finance.payment_ledger",
            "name": "收付款台账",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_payment_ledger",
                "action_xmlid": "smart_construction_core.action_payment_ledger",
            },
        },
        {
            "code": "cost.cost_compare",
            "name": "成本中心",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_cost_center",
                "action_xmlid": "smart_construction_core.action_project_cost_compare",
            },
        },
        {
            "code": "cost.project_budget",
            "name": "预算管理",
            "target": {
                "menu_xmlid": "smart_construction_core.menu_sc_project_budget",
                "action_xmlid": "smart_construction_core.action_project_budget",
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
            "name": "成本控制驾驶舱",
            "target": {
                "route": "/s/cost.control",
                "menu_xmlid": "smart_construction_core.menu_sc_project_cost_ledger",
                "action_xmlid": "smart_construction_core.action_project_cost_ledger",
            },
        },
        {
            "code": "cost.project_progress",
            "name": "进度填报",
            "target": {
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
                "menu_xmlid": "smart_construction_core.menu_sc_profit_reports",
                "action_xmlid": "smart_construction_core.action_project_profit_compare",
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
            "name": "工作台",
            "target": {"route": "/"},
        },
        {
            "code": "payments.approval",
            "name": "收付款审批中心",
            "target": {
                "route": "/s/payments.approval",
                "menu_xmlid": "smart_construction_core.menu_payment_request",
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
                "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
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
            "code": "quality.center",
            "name": "质量管理中心",
            "target": {"route": "/s/quality.center"},
        },
        {
            "code": "safety.center",
            "name": "安全管理中心",
            "target": {"route": "/s/safety.center"},
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
            "name": "工作台首页",
            "target": {"route": "/my-work"},
        },
    ]
