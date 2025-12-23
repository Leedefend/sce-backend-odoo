# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestActionGroupsGate(TransactionCase):
    """CI 守门：模块内 actions 必须有 groups，菜单/Action 不允许 URL 绕过。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_name = "smart_construction_core"
        cls.models = ["ir.actions.act_window", "ir.actions.server", "ir.actions.report"]

    def test_actions_have_groups(self):
        imd = self.env["ir.model.data"].search(
            [("module", "=", self.module_name), ("model", "in", self.models)]
        )
        missing = []
        for x in imd:
            act = self.env[x.model].browse(x.res_id)
            # 一些 action 类型可能不存在 groups_id 字段（极少），跳过
            if act.exists() and hasattr(act, "groups_id") and not act.groups_id:
                missing.append(f"{x.module}.{x.name}")
        self.assertFalse(
            missing,
            "Actions 缺少 groups_id（不允许 URL 绕过）：%s" % ", ".join(missing),
        )

    def test_menu_action_bypass(self):
        menus = self.env["ir.ui.menu"].search([])
        risky = []
        for menu in menus:
            if not menu.groups_id or not menu.action:
                continue
            act = menu.action
            if hasattr(act, "groups_id") and not act.groups_id:
                menu_xmlid = menu.get_external_id().get(menu.id) or ""
                act_xmlid = act.get_external_id().get(act.id) or ""
                risky.append(f"{menu_xmlid} -> {act_xmlid}")
        self.assertFalse(
            risky,
            "存在菜单有限流但 Action 无 groups 的绕过风险：%s" % ", ".join(risky),
        )
