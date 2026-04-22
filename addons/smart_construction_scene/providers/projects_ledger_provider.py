# -*- coding: utf-8 -*-
from __future__ import annotations


def build(scene_key: str = "projects.ledger", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    return {
        "scene_key": scene_key,
        "guidance": {
            "title": "项目台账",
            "message": "围绕项目台账、风险和关键跟进项组织项目工作入口。",
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
