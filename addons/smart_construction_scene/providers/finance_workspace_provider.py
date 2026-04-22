# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "finance.workspace", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "资金管理工作台",
            "message": "从 route-first 工作台入口继续处理财务跟进任务，并保持与财务中心根菜单一致的上下文。",
        },
        "primary_action": {
            "label": "进入资金工作台",
            "route": "/s/finance.workspace",
            "semantic": "finance_workspace_entry",
        },
        "fallback_strategy": {
            "type": "native_menu_compat",
            "menu_xmlid": "smart_construction_core.menu_sc_finance_center",
            "reason": "finance.workspace keeps finance root menu context but no longer claims native root action ownership",
        },
        "shared_root_compatibility": {
            "used": True,
            "closure_status": "route_plus_menu_compat",
            "owner_scene": "finance.center",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
