# -*- coding: utf-8 -*-
from __future__ import annotations


class CapabilityMatrixService:
    def __init__(self, env):
        self.env = env

    def build_matrix(self):
        sections = []
        for section in self._registry():
            items = []
            for item in section.get("items", []):
                resolved = self._resolve_item(item)
                items.append(resolved)
            items = [item for item in items if item.get("allowed")]
            if not items:
                continue
            items.sort(key=lambda item: (item.get("order", 1000), item.get("key", "")))
            sections.append(
                {
                    "key": section.get("key"),
                    "label": section.get("label"),
                    "items": items,
                }
            )
        return {"sections": sections}

    def _resolve_item(self, item):
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
            elif not menu._is_visible():
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

        action_id = action.id if action else None
        menu_id = menu.id if menu else None
        target_url = self._build_target_url(action, menu_id)

        return {
            "key": item.get("key"),
            "label": item.get("label"),
            "icon": item.get("icon"),
            "desc": item.get("desc"),
            "menu_xmlid": menu_xmlid,
            "action_xmlid": action_xmlid,
            "menu_id": menu_id,
            "action_id": action_id,
            "target_url": target_url,
            "allowed": allowed,
            "deny_reason": deny_reason,
            "order": item.get("order", 1000),
        }

    def _build_target_url(self, action, menu_id):
        if not action:
            return None
        if action._name == "ir.actions.act_url":
            return action.url
        if action._name == "ir.actions.act_window":
            url = f"/web#action={action.id}"
            if menu_id:
                url = f"/web#menu_id={menu_id}&action={action.id}"
            return url
        return None

    def _ref(self, xmlid):
        if not xmlid:
            return None
        return self.env.ref(xmlid, raise_if_not_found=False)

    def _registry(self):
        return [
            {
                "key": "project",
                "label": "项目",
                "items": [
                    {
                        "key": "project_board",
                        "label": "项目看板",
                        "desc": "生命周期看板与项目列表",
                        "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                        "action_xmlid": "smart_construction_core.action_sc_project_kanban_lifecycle",
                        "order": 10,
                    },
                    {
                        "key": "project_overview",
                        "label": "项目概览",
                        "desc": "项目总览与关键指标",
                        "menu_xmlid": "smart_construction_core.menu_sc_project_project",
                        "action_xmlid": "smart_construction_core.action_sc_project_overview",
                        "order": 20,
                    },
                ],
            },
            {
                "key": "contract",
                "label": "合同",
                "items": [
                    {
                        "key": "contract_income",
                        "label": "收入合同",
                        "desc": "收入合同与收款计划",
                        "menu_xmlid": "smart_construction_core.menu_sc_contract_income",
                        "action_xmlid": "smart_construction_core.action_construction_contract_income",
                        "order": 10,
                    },
                    {
                        "key": "contract_expense",
                        "label": "支出合同",
                        "desc": "支出合同与付款计划",
                        "menu_xmlid": "smart_construction_core.menu_sc_contract_expense",
                        "action_xmlid": "smart_construction_core.action_construction_contract_expense",
                        "order": 20,
                    },
                ],
            },
            {
                "key": "cost",
                "label": "成本",
                "items": [
                    {
                        "key": "cost_ledger",
                        "label": "成本台账",
                        "desc": "成本台账与进度录入",
                        "menu_xmlid": "smart_construction_core.menu_sc_project_cost_ledger",
                        "action_xmlid": "smart_construction_core.action_project_cost_ledger",
                        "order": 10,
                    },
                    {
                        "key": "project_budget",
                        "label": "项目预算",
                        "desc": "项目预算与调整",
                        "menu_xmlid": "smart_construction_core.menu_sc_project_budget",
                        "action_xmlid": "smart_construction_core.action_project_budget",
                        "order": 20,
                    },
                ],
            },
            {
                "key": "finance",
                "label": "财务",
                "items": [
                    {
                        "key": "payment_requests",
                        "label": "付款申请",
                        "desc": "付款申请与审批",
                        "menu_xmlid": "smart_construction_core.menu_payment_request",
                        "action_xmlid": "smart_construction_core.action_payment_request_my",
                        "order": 10,
                    },
                    {
                        "key": "treasury_ledger",
                        "label": "资金台账",
                        "desc": "资金台账与余额",
                        "menu_xmlid": "smart_construction_core.menu_sc_treasury_ledger",
                        "action_xmlid": "smart_construction_core.action_sc_treasury_ledger",
                        "order": 20,
                    },
                ],
            },
            {
                "key": "overview",
                "label": "概览",
                "items": [
                    {
                        "key": "capability_matrix",
                        "label": "能力矩阵",
                        "desc": "查看角色可用能力",
                        "menu_xmlid": "smart_construction_portal.menu_sc_portal_capability_matrix",
                        "action_xmlid": "smart_construction_portal.action_sc_portal_capability_matrix",
                        "order": 10,
                    },
                ],
            },
        ]
