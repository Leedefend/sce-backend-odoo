# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_scene.services.workflow_rollout_handoff import (
    build_direct_runtime_handoff,
)


def build(scene_key: str = "task.center", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    primary_action = {
        "label": "进入任务工作台",
        "action_xmlid": "project.action_view_all_task",
        "semantic": "task_work_center_entry",
    }
    fallback_strategy = {
        "type": "native_action_compat",
        "action_xmlid": "project.action_view_all_task",
        "reason": "keep the generic task native action available while task.center remains the canonical action-first work-center entry",
    }
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "任务工作台",
            "message": "从任务工作台进入任务列表、筛选和主动作处理，保持 action-first 的任务入口语义。",
        },
        "primary_action": primary_action,
        "fallback_strategy": fallback_strategy,
        "delivery_handoff_v1": build_direct_runtime_handoff(
            family="tasks",
            user_entry="action:project.action_view_all_task",
            final_scene="task.center",
            primary_action=primary_action,
            required_provider="construction.task_center_provider.v1|construction.task_board_provider.v1",
            fallback_policy=fallback_strategy,
        ),
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
