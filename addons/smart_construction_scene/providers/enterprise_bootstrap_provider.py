# -*- coding: utf-8 -*-
from __future__ import annotations


_GUIDANCE_BY_SCENE = {
    "enterprise.company": {
        "title": "企业信息",
        "message": "先补齐企业基础信息，保存后继续进入组织架构。",
        "next_scene": "enterprise.department",
    },
    "enterprise.department": {
        "title": "组织架构",
        "message": "先创建一级部门，再补齐二级和三级部门，最后进入用户设置。",
        "next_scene": "enterprise.post",
    },
    "enterprise.post": {
        "title": "岗位管理",
        "message": "补齐岗位主数据后，再进入用户设置给人员挂主岗位。",
        "next_scene": "enterprise.user",
    },
    "enterprise.user": {
        "title": "用户设置",
        "message": "给用户挂公司、部门、产品角色和初始密码，再用该账号登录验证首页入口。",
        "next_scene": "",
    },
}


def build(scene_key: str = "", runtime: dict | None = None, context: dict | None = None) -> dict:
    _ = context or {}
    runtime_payload = runtime or {}
    normalized_scene_key = str(scene_key or "").strip()
    guidance = _GUIDANCE_BY_SCENE.get(normalized_scene_key)
    if not guidance:
        return {}

    next_scene = str(guidance.get("next_scene") or "").strip()
    payload = {
        "scene_key": normalized_scene_key,
        "guidance": {
            "title": str(guidance.get("title") or normalized_scene_key).strip(),
            "message": str(guidance.get("message") or "").strip(),
        },
        "runtime": {
            "role_code": runtime_payload.get("role_code"),
            "company_id": runtime_payload.get("company_id"),
        },
    }
    if next_scene:
        payload["next_scene"] = next_scene
        payload["next_scene_route"] = f"/s/{next_scene}"
    return payload
