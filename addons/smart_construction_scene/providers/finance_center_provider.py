# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)
from odoo.addons.smart_construction_scene.services.handling_entry_catalog import (
    clone_finance_handling_entry_catalog,
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
    handling_catalog = clone_finance_handling_entry_catalog()
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "财务中心",
            "message": "以业务分类字典承载旧业务认知，左侧菜单收敛为综合办理入口，进入后按分类继续办理。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "handling_entry_catalog": handling_catalog,
        "extensions": {
            "handling_entry_catalog_v1": handling_catalog,
        },
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
