# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "contract.center", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    primary_action = {
        "label": "进入合同中心",
        "route": "/s/contract.center",
        "semantic": "contract_root_scene_entry",
    }
    fallback_strategy = {
        "type": "native_menu_compat",
        "menu_xmlid": "smart_construction_core.menu_sc_contract_center",
        "action_xmlid": "smart_construction_core.action_construction_contract_my",
        "reason": "keep native contract root menu/action available while contract.center remains canonical root owner",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "合同中心",
            "message": "先进入合同中心场景总览，再按工作台或监控分支继续处理合同任务。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "shared_root_compatibility": {
            "used": True,
            "closure_status": "root_owner_retained",
            "owner_scene": "contract.center",
        },
        "next_scene": "contracts.workspace",
        "next_scene_route": "/s/contracts.workspace",
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="contracts",
            user_entry="menu:smart_construction_core.menu_sc_contract_center",
            final_scene="contract.center",
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
