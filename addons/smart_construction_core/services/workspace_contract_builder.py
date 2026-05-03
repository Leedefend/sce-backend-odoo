# -*- coding: utf-8 -*-
from __future__ import annotations

from .scene_block_schema import action_target, build_contract, metric_card, native_view_ref, shortcut_grid, todo_list, warning_list


class WorkspaceContractBuilder:
    SOURCE_KIND = "workspace_home_odoo_native_capability_projection"
    SOURCE_AUTHORITIES = (
        "project.project",
        "payment.request",
        "sc.project.risk",
        "ir.actions",
        "ir.ui.menu",
        "res.groups",
        "odoo.orm",
    )

    def __init__(self, env):
        self.env = env

    @classmethod
    def source_authority_contract(cls):
        return {
            "kind": cls.SOURCE_KIND,
            "authorities": list(cls.SOURCE_AUTHORITIES),
            "projection_only": True,
            "no_business_fact_authority": True,
            "runtime_carrier": "workspace_scene_contract",
        }

    def _count(self, model_name, domain):
        if model_name not in self.env:
            return 0
        try:
            return self.env[model_name].search_count(domain)
        except Exception:
            return 0

    def build(self):
        project_total = self._count("project.project", [])
        active_projects = self._count("project.project", [("active", "=", True)])
        payment_pending = self._count("payment.request", [("state", "not in", ["done", "cancel"])])
        risk_open = self._count("sc.project.risk", [("state", "!=", "closed")])
        blocks = [
            metric_card(
                "project_total",
                "项目总数",
                project_total,
                subtitle="当前可见项目",
                target=action_target(action_xmlid="smart_construction_core.action_sc_project_list"),
            ),
            metric_card(
                "active_projects",
                "进行中项目",
                active_projects,
                subtitle="有效项目",
                target=action_target(action_xmlid="smart_construction_core.action_sc_project_my_list"),
            ),
            metric_card(
                "pending_payments",
                "待处理付款",
                payment_pending,
                subtitle="付款/收款申请",
                tone="warning" if payment_pending else "neutral",
                target=action_target(action_xmlid="smart_construction_core.action_payment_request_my"),
            ),
            shortcut_grid(
                "quick_entries",
                "快捷入口",
                [
                    {"key": "projects", "label": "项目台账", "target": action_target(action_xmlid="smart_construction_core.action_sc_project_list")},
                    {"key": "intake", "label": "项目立项", "target": action_target(action_xmlid="smart_construction_core.action_project_initiation")},
                    {"key": "payments", "label": "付款申请", "target": action_target(action_xmlid="smart_construction_core.action_payment_request_my")},
                    {"key": "contracts", "label": "合同汇总", "target": action_target(action_xmlid="smart_construction_core.action_project_contract_overview")},
                ],
            ),
            todo_list(
                "today_todos",
                "我的待办",
                [
                    {
                        "key": "payment_pending",
                        "title": "处理付款/收款申请",
                        "count": payment_pending,
                        "target": action_target(action_xmlid="smart_construction_core.action_payment_request_my"),
                    }
                ]
                if payment_pending
                else [],
            ),
            warning_list(
                "warnings",
                "预警",
                [
                    {
                        "key": "project_risk",
                        "title": "存在未关闭项目风险",
                        "count": risk_open,
                        "target": action_target(action_xmlid="smart_construction_core.action_sc_operating_drill_overpay_risk_pr"),
                    }
                ]
                if risk_open
                else [],
            ),
            native_view_ref(
                "project_list_ref",
                "项目列表摘要",
                action_xmlid="smart_construction_core.action_sc_project_list",
                model="project.project",
                view_mode="tree,kanban,form",
                count=project_total,
                summary="嵌入原生项目列表摘要，可继续打开完整列表/看板。",
            ),
        ]
        contract = build_contract(scene_key="workspace.home", title="角色首页", subtitle="今日任务、快捷入口与业务摘要", blocks=blocks)
        contract["source_authority"] = self.source_authority_contract()
        return contract
