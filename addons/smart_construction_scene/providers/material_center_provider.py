# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


SCENE_SPECS = {
    "material.center": {
        "title": "物资与分包",
        "message": "围绕材料档案、采购申请、验收、出入库、租赁和专业分包组织资源履约入口。",
        "label": "进入物资与分包",
        "route": "/s/material.center",
        "semantic": "material_resource_center_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_center",
        "family": "material_resource",
        "next_scene": "material.procurement",
        "next_scene_route": "/s/material.procurement",
    },
    "material.catalog": {
        "title": "材料档案",
        "message": "维护材料目录、规格型号和价格口径，作为采购、验收、库存和结算的基础数据。",
        "label": "进入材料档案",
        "route": "/s/material.catalog",
        "semantic": "material_catalog_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_catalog",
        "action_xmlid": "smart_construction_core.action_sc_material_product_template",
        "family": "material_catalog",
        "next_scene": "material.procurement",
        "next_scene_route": "/s/material.procurement",
    },
    "material.procurement": {
        "title": "采购协同",
        "message": "从材料计划和采购申请推进询比价、采购、验收入库和材料结算。",
        "label": "进入采购申请",
        "route": "/s/material.procurement",
        "semantic": "material_procurement_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_purchase_request",
        "action_xmlid": "smart_construction_core.action_sc_material_purchase_request",
        "family": "material_procurement",
        "next_scene": "material.acceptance",
        "next_scene_route": "/s/material.acceptance",
    },
    "material.acceptance": {
        "title": "材料进场验收",
        "message": "对进场材料执行验收、入库和出库跟踪，形成库存与结算依据。",
        "label": "进入材料验收",
        "route": "/s/material.acceptance",
        "semantic": "material_acceptance_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_acceptance",
        "action_xmlid": "smart_construction_core.action_sc_material_acceptance",
        "family": "material_acceptance",
        "next_scene": "material.settlement",
        "next_scene_route": "/s/material.settlement",
    },
    "material.settlement": {
        "title": "材料结算",
        "message": "按采购、验收和出入库链路汇总结算材料费用。",
        "label": "进入材料结算",
        "route": "/s/material.settlement",
        "semantic": "material_settlement_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_settlement",
        "action_xmlid": "smart_construction_core.action_sc_material_settlement",
        "family": "material_settlement",
    },
    "material.rental": {
        "title": "周转材料租赁",
        "message": "处理周转材料租赁计划、租赁单和租赁结算。",
        "label": "进入租赁计划",
        "route": "/s/material.rental",
        "semantic": "material_rental_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_material_rental_plan",
        "action_xmlid": "smart_construction_core.action_sc_material_rental_plan",
        "family": "material_rental",
    },
    "subcontract.management": {
        "title": "专业分包",
        "message": "按分包计划、申请、登记和结算组织专业分包全过程履约。",
        "label": "进入分包计划",
        "route": "/s/subcontract.management",
        "semantic": "subcontract_management_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_subcontract_plan",
        "action_xmlid": "smart_construction_core.action_sc_subcontract_plan",
        "family": "subcontract_management",
    },
}


def build(scene_key: str = "material.center", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    spec = dict(SCENE_SPECS.get(scene_key) or SCENE_SPECS["material.center"])
    primary_action = {
        "label": spec["label"],
        "route": spec["route"],
        "semantic": spec["semantic"],
    }
    if spec.get("menu_xmlid"):
        primary_action["menu_xmlid"] = spec["menu_xmlid"]
    if spec.get("action_xmlid"):
        primary_action["action_xmlid"] = spec["action_xmlid"]

    fallback_strategy = {
        "type": "native_menu_compat",
        "menu_xmlid": spec.get("menu_xmlid"),
        "action_xmlid": spec.get("action_xmlid"),
        "reason": "keep construction native material and subcontract actions available while scene handoff owns the industry workflow entry",
    }
    payload = {
        "scene_key": scene_key,
        "guidance": {
            "title": spec["title"],
            "message": spec["message"],
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family=spec["family"],
            user_entry=f"menu:{spec.get('menu_xmlid')}",
            final_scene=scene_key,
            primary_action=primary_action,
            required_provider="construction.material_center_provider.v1",
            fallback_policy=fallback_strategy,
            rollout_wave="wave_2",
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
    if spec.get("next_scene"):
        payload["next_scene"] = spec["next_scene"]
        payload["next_scene_route"] = spec.get("next_scene_route")
    return payload
