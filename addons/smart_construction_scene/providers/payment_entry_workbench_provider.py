# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "finance.payment_requests", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    canonical_action = "smart_construction_core.action_payment_request_my"
    compatibility_action = "smart_construction_core.action_payment_request"
    primary_action = {
        "label": "进入我的付款申请",
        "action_xmlid": canonical_action,
        "semantic": "payment_request_personal_entry",
    }
    fallback_strategy = {
        "type": "native_action_compat",
        "action_xmlid": compatibility_action,
        "reason": "keep the generic payment request native action available while finance.payment_requests remains the canonical personal-entry list scene",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "付款申请列表",
            "message": "从个人付款申请列表进入 payment-entry 主入口，保持 personal-entry 语义，同时保留通用原生列表作为兼容入口。",
        },
        "primary_action": primary_action,
        "next_action": {
            "label": "处理付款申请列表",
            "action_xmlid": canonical_action,
            "semantic": "payment_request_list_queue",
        },
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="payment_entry",
            user_entry="menu:smart_construction_core.menu_payment_request",
            final_scene="finance.payment_requests",
            primary_action=primary_action,
            required_provider="construction.payment_entry_workbench_provider.v1",
            fallback_policy=fallback_strategy,
            rollout_wave="wave_2_held",
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
