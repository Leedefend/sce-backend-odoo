# -*- coding: utf-8 -*-
from __future__ import annotations


def list_bundle_scenes() -> list[dict]:
    return [
        {
            "code": "owner.dashboard",
            "name": "业主驾驶舱",
            "target": {"scene_key": "owner.dashboard", "route": "/workbench?scene=owner.dashboard"},
            "tiles": [
                {"key": "owner.dashboard.open", "label": "业主驾驶舱", "required_capabilities": ["owner.dashboard.open"]},
            ],
        },
        {
            "code": "owner.projects.list",
            "name": "业主项目列表",
            "target": {"scene_key": "owner.projects.list", "route": "/workbench?scene=owner.projects.list"},
            "tiles": [
                {"key": "owner.projects.list", "label": "项目列表", "required_capabilities": ["owner.projects.list"]},
                {"key": "owner.projects.detail", "label": "项目详情", "required_capabilities": ["owner.projects.detail"]},
                {"key": "owner.risk.list", "label": "风险清单", "required_capabilities": ["owner.risk.list"]},
            ],
        },
        {
            "code": "owner.payment.center",
            "name": "业主付款中心",
            "target": {"scene_key": "owner.payment.center", "route": "/workbench?scene=owner.payment.center"},
            "tiles": [
                {
                    "key": "owner.payment_request.submit",
                    "label": "提交付款申请",
                    "required_capabilities": ["owner.payment_request.submit"],
                },
                {
                    "key": "owner.payment_request.approve",
                    "label": "审批付款申请",
                    "required_capabilities": ["owner.payment_request.approve"],
                },
            ],
        },
        {
            "code": "owner.report.overview",
            "name": "业主经营总览",
            "target": {"scene_key": "owner.report.overview", "route": "/workbench?scene=owner.report.overview"},
            "tiles": [
                {"key": "owner.report.overview", "label": "经营总览", "required_capabilities": ["owner.report.overview"]},
                {"key": "owner.approval.center", "label": "审批中心", "required_capabilities": ["owner.approval.center"]},
            ],
        },
    ]


def list_bundle_capabilities() -> list[dict]:
    return [
        {
            "key": "owner.dashboard.open",
            "name": "业主驾驶舱",
            "ui_label": "业主驾驶舱",
            "ui_hint": "查看业主侧关键经营与审批指标",
            "intent": "ui.contract",
            "group_key": "owner_management",
            "group_label": "业主管理",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.dashboard", "route": "/workbench?scene=owner.dashboard"},
            "required_roles": ["owner"],
            "required_groups": [],
        },
        {
            "key": "owner.projects.list",
            "name": "业主项目列表",
            "ui_label": "项目列表",
            "ui_hint": "查看业主侧项目列表与状态",
            "intent": "owner.projects.list",
            "group_key": "owner_management",
            "group_label": "业主管理",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.projects.list", "route": "/workbench?scene=owner.projects.list"},
            "required_roles": ["owner"],
            "required_groups": [],
        },
        {
            "key": "owner.projects.detail",
            "name": "业主项目详情",
            "ui_label": "项目详情",
            "ui_hint": "查看业主侧项目详情与关键指标",
            "intent": "owner.projects.detail",
            "group_key": "owner_management",
            "group_label": "业主管理",
            "version": "v1",
            "state": "READY",
            "capability_state": "readonly",
            "default_payload": {"scene_key": "owner.projects.list", "route": "/workbench?scene=owner.projects.list"},
            "required_roles": ["owner"],
            "required_groups": [],
        },
        {
            "key": "owner.risk.list",
            "name": "业主风险清单",
            "ui_label": "风险清单",
            "ui_hint": "查看业主侧风险项与跟踪状态",
            "intent": "owner.risk.list",
            "group_key": "owner_management",
            "group_label": "业主管理",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.projects.list", "route": "/workbench?scene=owner.projects.list"},
            "required_roles": ["owner"],
            "required_groups": [],
        },
        {
            "key": "owner.payment_request.submit",
            "name": "业主付款提交",
            "ui_label": "业主付款提交",
            "ui_hint": "提交业主付款申请",
            "intent": "owner.payment.request.submit",
            "group_key": "owner_finance",
            "group_label": "业主财务",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.payment.center", "route": "/workbench?scene=owner.payment.center"},
            "required_roles": ["owner"],
            "required_groups": ["smart_core.group_smart_core_data_operator"],
        },
        {
            "key": "owner.payment_request.approve",
            "name": "业主付款审批",
            "ui_label": "业主付款审批",
            "ui_hint": "审批业主付款申请",
            "intent": "owner.payment.request.approve",
            "group_key": "owner_finance",
            "group_label": "业主财务",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.payment.center", "route": "/workbench?scene=owner.payment.center"},
            "required_roles": ["owner"],
            "required_groups": ["smart_core.group_smart_core_finance_approver"],
        },
        {
            "key": "owner.report.overview",
            "name": "业主经营总览",
            "ui_label": "经营总览",
            "ui_hint": "查看业主侧经营总览与趋势",
            "intent": "owner.report.overview",
            "group_key": "owner_analytics",
            "group_label": "业主分析",
            "version": "v1",
            "state": "READY",
            "capability_state": "allow",
            "default_payload": {"scene_key": "owner.report.overview", "route": "/workbench?scene=owner.report.overview"},
            "required_roles": ["owner", "executive"],
            "required_groups": [],
        },
        {
            "key": "owner.approval.center",
            "name": "业主审批中心",
            "ui_label": "审批中心",
            "ui_hint": "统一处理业主侧审批任务",
            "intent": "owner.approval.center",
            "group_key": "owner_finance",
            "group_label": "业主财务",
            "version": "v1",
            "state": "READY",
            "capability_state": "pending",
            "default_payload": {"scene_key": "owner.report.overview", "route": "/workbench?scene=owner.report.overview"},
            "required_roles": ["owner"],
            "required_groups": ["smart_core.group_smart_core_finance_approver"],
        },
    ]


def recommended_roles() -> list[str]:
    return ["owner", "executive", "finance"]


def default_dashboard() -> str:
    return "owner.dashboard"
