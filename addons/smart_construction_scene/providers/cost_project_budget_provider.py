# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "cost.project_budget", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "预算管理",
            "message": "围绕项目预算、分配与成本控制组织预算管理入口。",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
