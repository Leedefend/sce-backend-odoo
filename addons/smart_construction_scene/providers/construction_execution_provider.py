# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


SCENE_SPECS = {
    "construction.execution": {
        "title": "施工管理",
        "message": "围绕计划、汇报、施工日志、质量和安全闭环组织现场执行。",
        "label": "进入施工管理",
        "route": "/s/construction.execution",
        "semantic": "construction_execution_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_construction_management_center",
        "family": "construction_execution",
        "next_scene": "construction.plan",
        "next_scene_route": "/s/construction.plan",
    },
    "construction.plan": {
        "title": "计划管理",
        "message": "维护项目施工计划、版本和分解明细。",
        "label": "进入计划管理",
        "route": "/s/construction.plan",
        "semantic": "construction_plan_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_plan",
        "action_xmlid": "smart_construction_core.action_sc_plan",
        "family": "construction_execution",
        "next_scene": "construction.plan_report",
        "next_scene_route": "/s/construction.plan_report",
    },
    "construction.plan_report": {
        "title": "计划汇报",
        "message": "按计划节点汇报现场进展、偏差和风险。",
        "label": "进入计划汇报",
        "route": "/s/construction.plan_report",
        "semantic": "construction_plan_report_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_plan_report",
        "action_xmlid": "smart_construction_core.action_sc_plan_report",
        "family": "construction_execution",
        "next_scene": "construction.diary",
        "next_scene_route": "/s/construction.diary",
    },
    "construction.diary": {
        "title": "施工日志",
        "message": "记录每日施工、人员机械、材料和现场情况。",
        "label": "进入施工日志",
        "route": "/s/construction.diary",
        "semantic": "construction_diary_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_construction_diary",
        "action_xmlid": "smart_construction_core.action_sc_construction_diary",
        "family": "construction_execution",
    },
    "quality.center": {
        "title": "质量检查",
        "message": "登记质量问题并推动整改、复验闭环。",
        "label": "进入质量检查",
        "route": "/s/quality.center",
        "semantic": "quality_issue_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_quality_issue",
        "action_xmlid": "smart_construction_core.action_sc_quality_issue",
        "family": "quality_closure",
        "next_scene": "quality.rectification",
        "next_scene_route": "/s/quality.rectification",
    },
    "quality.rectification": {
        "title": "质量整改",
        "message": "跟踪质量问题整改责任、整改动作和完成情况。",
        "label": "进入质量整改",
        "route": "/s/quality.rectification",
        "semantic": "quality_rectification_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_quality_rectification",
        "action_xmlid": "smart_construction_core.action_sc_quality_rectification",
        "family": "quality_closure",
        "next_scene": "quality.recheck",
        "next_scene_route": "/s/quality.recheck",
    },
    "quality.recheck": {
        "title": "质量复验",
        "message": "对整改结果进行复验确认，形成质量闭环。",
        "label": "进入质量复验",
        "route": "/s/quality.recheck",
        "semantic": "quality_recheck_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_quality_recheck",
        "action_xmlid": "smart_construction_core.action_sc_quality_recheck",
        "family": "quality_closure",
    },
    "safety.center": {
        "title": "安全检查",
        "message": "登记安全问题并推动整改、复验闭环。",
        "label": "进入安全检查",
        "route": "/s/safety.center",
        "semantic": "safety_issue_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_safety_issue",
        "action_xmlid": "smart_construction_core.action_sc_safety_issue",
        "family": "safety_closure",
        "next_scene": "safety.rectification",
        "next_scene_route": "/s/safety.rectification",
    },
    "safety.rectification": {
        "title": "安全整改",
        "message": "跟踪安全问题整改责任、整改动作和完成情况。",
        "label": "进入安全整改",
        "route": "/s/safety.rectification",
        "semantic": "safety_rectification_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_safety_rectification",
        "action_xmlid": "smart_construction_core.action_sc_safety_rectification",
        "family": "safety_closure",
        "next_scene": "safety.recheck",
        "next_scene_route": "/s/safety.recheck",
    },
    "safety.recheck": {
        "title": "安全复验",
        "message": "对整改结果进行复验确认，形成安全闭环。",
        "label": "进入安全复验",
        "route": "/s/safety.recheck",
        "semantic": "safety_recheck_entry",
        "menu_xmlid": "smart_construction_core.menu_sc_safety_recheck",
        "action_xmlid": "smart_construction_core.action_sc_safety_recheck",
        "family": "safety_closure",
    },
}


def build(scene_key: str = "construction.execution", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    spec = dict(SCENE_SPECS.get(scene_key) or SCENE_SPECS["construction.execution"])
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
        "reason": "keep construction native execution actions available while scene handoff owns the industry workflow entry",
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
            required_provider="construction.execution_provider.v1",
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
