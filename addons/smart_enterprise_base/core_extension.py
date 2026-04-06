# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


def get_intent_handler_contributions():
    return []


def _resolve_action_target(env, action_xmlid: str, menu_xmlid: str) -> dict:
    action = env.ref(action_xmlid, raise_if_not_found=False)
    menu = env.ref(menu_xmlid, raise_if_not_found=False)
    return {
        "action_id": int(action.id) if action else 0,
        "menu_id": int(menu.id) if menu else 0,
        "action_xmlid": action_xmlid,
        "menu_xmlid": menu_xmlid,
        "route": f"/a/{int(action.id)}" if action else "",
    }


def smart_core_extend_system_init(data, env, user):
    try:
        ext_facts = data.get("ext_facts") if isinstance(data.get("ext_facts"), dict) else {}
        enablement = ext_facts.get("enterprise_enablement") if isinstance(ext_facts.get("enterprise_enablement"), dict) else {}
        company_id = int(user.company_id.id or env.company.id or 0) if (user.company_id or env.company) else 0
        department_count = env["hr.department"].sudo().search_count([("company_id", "=", company_id)]) if company_id else 0
        managed_user_count = env["res.users"].sudo().search_count(
            [
                ("share", "=", False),
                ("id", "!=", user.id),
                ("company_ids", "in", [company_id]),
            ]
        ) if company_id else 0
        company_target = _resolve_action_target(
            env,
            "smart_enterprise_base.action_enterprise_company",
            "smart_enterprise_base.menu_enterprise_company",
        )
        department_target = _resolve_action_target(
            env,
            "smart_enterprise_base.action_enterprise_department",
            "smart_enterprise_base.menu_enterprise_department",
        )
        user_target = _resolve_action_target(
            env,
            "smart_enterprise_base.action_enterprise_user",
            "smart_enterprise_base.menu_enterprise_user",
        )
        company_status = "done" if company_id else "active"
        department_status = "done" if department_count > 0 else ("active" if company_status == "done" else "pending")
        user_status = "active" if department_count > 0 else "pending"
        if managed_user_count > 0:
            user_status = "done"
        primary_action = company_target
        if company_status == "done" and department_status != "done":
            primary_action = department_target
        elif company_status == "done" and department_status == "done":
            primary_action = user_target
        enablement["mainline"] = {
            "version": "v1",
            "phase": "sprint1" if department_count > 0 else "sprint0",
            "theme": "company_department_user_role_bootstrap" if department_count > 0 else "company_department_user_bootstrap",
            "entry_root_xmlid": "smart_enterprise_base.menu_enterprise_base_root",
            "steps": [
                {
                    "key": "company",
                    "label": "公司信息",
                    "status": company_status,
                    "entry_xmlid": "smart_enterprise_base.menu_enterprise_company",
                    "action_xmlid": "smart_enterprise_base.action_enterprise_company",
                    "next_hint": "保存公司后进入组织架构",
                    "target": company_target,
                },
                {
                    "key": "department",
                    "label": "组织架构",
                    "status": department_status,
                    "entry_xmlid": "smart_enterprise_base.menu_enterprise_department",
                    "action_xmlid": "smart_enterprise_base.action_enterprise_department",
                    "next_hint": "先创建一级部门，再补齐二级和三级部门",
                    "target": department_target,
                },
                {
                    "key": "user",
                    "label": "用户设置",
                    "status": user_status,
                    "entry_xmlid": "smart_enterprise_base.menu_enterprise_user",
                    "action_xmlid": "smart_enterprise_base.action_enterprise_user",
                    "next_hint": "给用户挂公司、部门、产品角色和初始密码，再用该账号登录验证首页入口",
                    "target": user_target,
                },
            ],
            "current_company_id": company_id,
            "current_company_name": user.company_id.display_name if user.company_id else (env.company.display_name if env.company else ""),
            "primary_action": primary_action,
        }
        ext_facts["enterprise_enablement"] = enablement
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_enterprise_base] extend system.init failed: %s", exc)
