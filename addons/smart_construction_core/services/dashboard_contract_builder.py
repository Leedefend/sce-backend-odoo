# -*- coding: utf-8 -*-
from __future__ import annotations

from .scene_block_schema import action_target, build_contract, metric_card, native_view_ref, shortcut_grid, warning_list


class DashboardContractBuilder:
    def __init__(self, env):
        self.env = env

    def _count(self, model_name, domain):
        if model_name not in self.env:
            return 0
        try:
            return self.env[model_name].search_count(domain)
        except Exception:
            return 0

    def build(self):
        projects = self._count("project.project", [])
        payments = self._count("payment.request", [])
        budgets = self._count("project.budget", [("active", "=", True)])
        cost_rows = self._count("project.cost.ledger", [])
        warnings = []
        pending_payment = self._count("payment.request", [("state", "not in", ["done", "cancel"])])
        if pending_payment:
            warnings.append(
                {
                    "key": "pending_payment",
                    "title": "存在待处理付款/收款申请",
                    "count": pending_payment,
                    "target": action_target(action_xmlid="smart_construction_core.action_payment_request_my"),
                }
            )
        blocks = [
            metric_card(
                "company_projects",
                "项目规模",
                projects,
                subtitle="公司可见项目",
                target=action_target(action_xmlid="smart_construction_core.action_sc_project_list"),
            ),
            metric_card(
                "payment_documents",
                "收付款单据",
                payments,
                subtitle="付款/收款申请",
                target=action_target(action_xmlid="smart_construction_core.action_payment_request_my"),
            ),
            metric_card(
                "active_budgets",
                "有效预算",
                budgets,
                subtitle="项目预算版本",
                target=action_target(action_xmlid="smart_construction_core.action_project_budget"),
            ),
            metric_card(
                "cost_ledger_rows",
                "成本台账",
                cost_rows,
                subtitle="成本记录行",
                target=action_target(action_xmlid="smart_construction_core.action_project_cost_ledger"),
            ),
            warning_list("company_warnings", "经营预警", warnings),
            shortcut_grid(
                "dashboard_shortcuts",
                "分析入口",
                [
                    {"key": "finance", "label": "财务中心", "target": action_target(action_xmlid="smart_construction_core.action_payment_request_my")},
                    {"key": "cost", "label": "成本台账", "target": action_target(action_xmlid="smart_construction_core.action_project_cost_ledger")},
                    {"key": "fund", "label": "资金日报", "target": action_target(action_xmlid="smart_construction_core.action_sc_fund_daily_summary")},
                    {"key": "operate", "label": "经营指标", "target": action_target(action_xmlid="smart_construction_core.action_sc_operating_metrics_project")},
                ],
            ),
            native_view_ref(
                "project_dashboard_ref",
                "项目看板摘要",
                action_xmlid="smart_construction_core.action_project_dashboard",
                model="project.project",
                view_mode="kanban,tree,form",
                count=projects,
                summary="可打开原生项目看板作为明细承载，当前页面本身由场景契约渲染。",
            ),
        ]
        return build_contract(scene_key="dashboard.company", title="公司驾驶舱", subtitle="公司级经营、资金与成本摘要", blocks=blocks)
