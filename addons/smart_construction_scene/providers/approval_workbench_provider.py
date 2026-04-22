# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "payments.approval", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    action_xmlid = "smart_construction_core.action_sc_tier_review_my_payment_request"
    primary_action = {
        "label": "进入付款审批",
        "action_xmlid": action_xmlid,
        "semantic": "payment_approval_workbench_entry",
    }
    fallback_strategy = {
        "type": "native_action_compat",
        "action_xmlid": action_xmlid,
        "reason": "keep the native approval action available while payments.approval remains the canonical approval-specific workbench entry",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "付款审批工作台",
            "message": "从审批工作台进入个人待审付款请求，保持 approval-first 的动作语义，不回退到通用付款列表。",
        },
        "primary_action": primary_action,
        "next_action": {
            "label": "处理待审付款请求",
            "action_xmlid": action_xmlid,
            "semantic": "payment_approval_queue",
        },
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="payment_approval",
            user_entry="menu:smart_construction_core.menu_sc_tier_review_my_payment_request",
            final_scene="payments.approval",
            primary_action=primary_action,
            required_provider="construction.approval_workbench_provider.v1",
            fallback_policy=fallback_strategy,
            rollout_wave="wave_2_held",
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
