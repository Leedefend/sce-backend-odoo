# -*- coding: utf-8 -*-
from __future__ import annotations


def list_owner_scenes() -> list[dict]:
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
                {
                    "key": "owner.projects.list",
                    "label": "项目列表",
                    "required_capabilities": ["owner.projects.list"],
                },
                {
                    "key": "owner.projects.detail",
                    "label": "项目详情",
                    "required_capabilities": ["owner.projects.detail"],
                },
                {
                    "key": "owner.risk.list",
                    "label": "风险清单",
                    "required_capabilities": ["owner.risk.list"],
                },
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
                {
                    "key": "owner.report.overview",
                    "label": "经营总览",
                    "required_capabilities": ["owner.report.overview"],
                },
                {
                    "key": "owner.approval.center",
                    "label": "审批中心",
                    "required_capabilities": ["owner.approval.center"],
                },
            ],
        },
    ]
