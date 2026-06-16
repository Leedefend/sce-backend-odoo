# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.handling_entry_catalog import (
    clone_finance_handling_entry_catalog,
)


def build(scene_key: str = "finance.workspace", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    handling_catalog = clone_finance_handling_entry_catalog()
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "资金管理工作台",
            "message": "按综合办理入口承载收付、税票、费用和资金往来，旧业务认知保留为业务分类。",
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
        "handling_entry_catalog": handling_catalog,
        "extensions": {
            "handling_entry_catalog_v1": handling_catalog,
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
