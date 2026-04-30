# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "projects.list", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    primary_action = {
        "label": "进入项目台账",
        "action_xmlid": "smart_construction_core.action_sc_project_list",
        "semantic": "projects_list_entry",
    }
    fallback_strategy = {
        "type": "native_menu_action_compat",
        "menu_xmlid": "smart_construction_core.menu_sc_root",
        "action_xmlid": "smart_construction_core.action_sc_project_list",
        "reason": "keep the native project root menu/action available while projects.list remains the canonical wave-1 handoff entry",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "项目台账",
            "message": "从统一台账入口查看项目状态、排序和批量动作。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="projects",
            user_entry="menu:smart_construction_core.menu_sc_root",
            final_scene="projects.list",
            primary_action=primary_action,
            required_provider="construction.projects_ledger_provider.v1|construction.projects_detail_provider.v1",
            fallback_policy=fallback_strategy,
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
