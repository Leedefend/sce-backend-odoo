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
    ]

