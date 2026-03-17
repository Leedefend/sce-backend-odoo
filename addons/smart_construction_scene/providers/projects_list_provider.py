# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "projects.list", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "项目列表",
            "message": "从编排后的列表入口查看项目状态、排序和批量动作。",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }

