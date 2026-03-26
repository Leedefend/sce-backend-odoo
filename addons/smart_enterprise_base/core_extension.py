# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)


def smart_core_register(registry):
    return registry


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
        enablement["mainline"] = {
            "version": "v1",
            "phase": "sprint0",
            "theme": "company_department_bootstrap",
            "entry_root_xmlid": "smart_enterprise_base.menu_enterprise_base_root",
            "steps": [
                {
                    "key": "company",
                    "label": "公司信息",
                    "status": "active",
                    "entry_xmlid": "smart_enterprise_base.menu_enterprise_company",
                    "action_xmlid": "smart_enterprise_base.action_enterprise_company",
                    "next_hint": "保存公司后进入组织架构",
                    "target": company_target,
                },
                {
                    "key": "department",
                    "label": "组织架构",
                    "status": "pending",
                    "entry_xmlid": "smart_enterprise_base.menu_enterprise_department",
                    "action_xmlid": "smart_enterprise_base.action_enterprise_department",
                    "next_hint": "先创建一级部门，再补齐二级和三级部门",
                    "target": department_target,
                },
            ],
            "current_company_id": int(user.company_id.id or 0) if user.company_id else 0,
            "primary_action": company_target,
        }
        ext_facts["enterprise_enablement"] = enablement
        data["ext_facts"] = ext_facts
    except Exception as exc:
        _logger.warning("[smart_enterprise_base] extend system.init failed: %s", exc)
