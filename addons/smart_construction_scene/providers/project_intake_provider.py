# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "projects.intake", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "项目立项引导",
            "message": "优先填写项目名称、负责人、开始日期，创建后自动进入下一场景。",
        },
        "next_scene": "project.management",
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }

