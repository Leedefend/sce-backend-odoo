# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_gate", "security_gate")
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

    def test_business_entity_entry_uses_business_config_group(self):
        expected_group = self.env.ref("smart_construction_core.group_sc_cap_business_config_admin")
        action = self.env.ref("smart_construction_core.action_sc_business_entity")
        menu = self.env.ref("smart_construction_core.menu_sc_business_entity")
        legacy_action = self.env.ref("smart_construction_core.action_sc_legacy_business_entity_map")
        legacy_menu = self.env.ref("smart_construction_core.menu_sc_legacy_business_entity_map")

        self.assertEqual(action.groups_id, expected_group)
        self.assertEqual(menu.groups_id, expected_group)
        self.assertNotIn(expected_group, legacy_action.groups_id)
        self.assertNotIn(expected_group, legacy_menu.groups_id)

    def test_business_config_user_can_read_business_entity_action_payload(self):
        group = self.env.ref("smart_construction_core.group_sc_cap_business_config_admin")
        company = self.env.ref("base.main_company")
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "action_payload_business_config",
                "login": "action_payload_business_config",
                "email": "action_payload_business_config@example.com",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "groups_id": [(6, 0, [group.id])],
            }
        )
        action = self.env.ref("smart_construction_core.action_sc_business_entity").with_user(user)

        payload = action.read()[0]

        self.assertEqual(payload["res_model"], "sc.business.entity")
        self.assertEqual(payload["id"], action.id)
