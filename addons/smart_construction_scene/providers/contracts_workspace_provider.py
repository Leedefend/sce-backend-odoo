# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "contracts.workspace", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    primary_action = {
        "label": "进入合同工作台",
        "route": "/s/contracts.workspace",
        "semantic": "contract_workspace_entry",
    }
    fallback_strategy = {
        "type": "native_action_compat",
        "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
        "action_xmlid": "smart_construction_core.action_construction_contract_my",
        "reason": "contracts.workspace keeps contract root menu/action context without claiming a new family root authority",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "合同工作台",
            "message": "从 route-first 合同工作台入口继续处理合同跟进任务，并保持与合同中心根入口一致的上下文。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="contracts",
            user_entry="route:/s/contracts.workspace",
            final_scene="contracts.workspace",
            primary_action=primary_action,
            required_provider="construction.contract_center_provider.v1|construction.contracts_workspace_provider.v1",
            fallback_policy=fallback_strategy,
            rollout_wave="wave_2",
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
