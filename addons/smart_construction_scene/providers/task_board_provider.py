# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "task.board", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "任务看板",
            "message": "从 route-first 的任务看板入口继续处理板式任务流，同时保持与 task.center 分离的工作语义。",
        },
        "primary_action": {
            "label": "进入任务看板",
            "route": "/s/task.board",
            "semantic": "task_board_entry",
        },
        "fallback_strategy": {
            "type": "route_compat",
            "route": "/s/task.board",
            "reason": "task.board stays as a route-first compat carrier without claiming native task action ownership",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
