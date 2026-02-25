# -*- coding: utf-8 -*-
from __future__ import annotations


def list_owner_capabilities() -> list[dict]:
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
            "required_groups": ["smart_core.group_sc_data_operator"],
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
            "required_groups": ["smart_core.group_sc_finance_approver"],
        },
    ]

