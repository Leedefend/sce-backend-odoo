# -*- coding: utf-8 -*-
from __future__ import annotations


class PortalDashboardService:
    def __init__(self, env):
        self.env = env

    def build_dashboard(self):
        entries = []
        for item in self._registry():
            resolved = self._resolve_entry(item)
            if not resolved.get("allowed"):
                continue
            entries.append(resolved)
        return {
            "entries": entries,
        }

    def _resolve_entry(self, item):
        menu_xmlid = item.get("menu_xmlid")
        action_xmlid = item.get("action_xmlid")
        menu = self._ref(menu_xmlid)
        action = self._ref(action_xmlid)

        allowed = True
        deny_reason = []
        if menu_xmlid:
            if not menu:
                allowed = False
                deny_reason.append("menu_not_found")
            elif not self._menu_visible(menu):
                allowed = False
                deny_reason.append("menu_not_visible")
        if action_xmlid:
            if not action:
                allowed = False
                deny_reason.append("action_not_found")
            else:
                groups = getattr(action, "groups_id", None)
                if groups and not (groups & self.env.user.groups_id):
                    allowed = False
                    deny_reason.append("action_forbidden")

        target = self._build_target(action, menu.id if menu else None)

        return {
            "key": item.get("key"),
            "label": item.get("label"),
            "icon": item.get("icon"),
            "desc": item.get("desc"),
            "menu_xmlid": menu_xmlid,
            "action_xmlid": action_xmlid,
            "menu_id": menu.id if menu else None,
            "action_id": action.id if action else None,
            "target": target,
            "allowed": allowed,
            "deny_reason": deny_reason,
        }

    def _build_target(self, action, menu_id):
        if not action:
            return None
        if action._name == "ir.actions.act_url":
            return {"type": "url", "value": action.url}
        if action._name == "ir.actions.act_window":
            if menu_id:
                return {"type": "action", "value": f"/web#menu_id={menu_id}&action={action.id}"}
            return {"type": "action", "value": f"/web#action={action.id}"}
        return None

    def _menu_visible(self, menu):
        if hasattr(menu, "_is_visible"):
            return bool(menu._is_visible())
        groups = getattr(menu, "groups_id", None)
        if groups and not (groups & self.env.user.groups_id):
            return False
        return True

    def _ref(self, xmlid):
        if not xmlid:
            return None
        return self.env.ref(xmlid, raise_if_not_found=False)

    def _registry(self):
        return [
            {
                "key": "project_work",
                "label": "项目工作",
                "icon": "P",
                "desc": "项目看板与概览入口",
                "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
            },
            {
                "key": "contract_work",
                "label": "合同工作",
                "icon": "C",
                "desc": "合同台账与合同清单",
                "menu_xmlid": "smart_construction_core.menu_sc_contract_income",
                "action_xmlid": "smart_construction_core.action_construction_contract_my",
            },
            {
                "key": "cost_work",
                "label": "成本工作",
                "icon": "K",
                "desc": "成本台账与预算入口",
                "menu_xmlid": "smart_construction_core.menu_sc_project_cost_ledger",
                "action_xmlid": "smart_construction_core.action_project_cost_ledger_my",
            },
            {
                "key": "finance_work",
                "label": "财务工作",
                "icon": "F",
                "desc": "付款申请与财务台账",
                "menu_xmlid": "smart_construction_core.menu_payment_request",
                "action_xmlid": "smart_construction_core.action_payment_request_my",
            },
            {
                "key": "capability_matrix",
                "label": "能力矩阵",
                "icon": "M",
                "desc": "查看角色可用能力",
                "menu_xmlid": "smart_construction_portal.menu_sc_portal_capability_matrix",
                "action_xmlid": "smart_construction_portal.action_sc_portal_capability_matrix",
            },
        ]
