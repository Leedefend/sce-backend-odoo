# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "projects.detail", runtime: dict | None = None, context: dict | None = None) -> dict:
    context_payload = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "项目详情",
            "message": "从项目详情入口继续处理台账后的明细工作与下一步动作。",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
            "record_id": context_payload.get("record_id") or runtime_payload.get("record_id"),
        },
    }
