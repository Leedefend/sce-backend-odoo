# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "finance.center", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    primary_action = {
        "label": "进入财务中心",
        "route": "/s/finance.center",
        "semantic": "finance_root_entry",
    }
    fallback_strategy = {
        "type": "native_menu_compat",
        "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
        "action_xmlid": "smart_construction_core.action_sc_finance_dashboard",
        "reason": "keep native finance root menu/action available while finance.center remains canonical root owner",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "财务中心",
            "message": "先从财务中心总览进入资金主入口，再按工作台分流到收付与跟进动作。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "shared_root_compatibility": {
            "used": True,
            "closure_status": "root_owner_retained",
            "owner_scene": "finance.center",
        },
        "next_scene": "finance.workspace",
        "next_scene_route": "/s/finance.workspace",
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="finance_center",
            user_entry="menu:smart_construction_core.menu_sc_finance_center",
            final_scene="finance.center",
            primary_action=primary_action,
            required_provider="construction.finance_center_provider.v1|construction.finance_workspace_provider.v1",
            fallback_policy=fallback_strategy,
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
