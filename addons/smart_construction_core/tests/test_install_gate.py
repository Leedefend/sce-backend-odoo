# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("at_install", "-post_install", "sc_install", "sc_gate")
class TestInstallGate(TransactionCase):
    """Install Gate：安装期结构完整性（xmlid 存在、关键入口有 groups）。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module = "smart_construction_core"
        cls.imd = cls.env["ir.model.data"].sudo()
        cls.action_models = [
            "ir.actions.act_window",
            "ir.actions.server",
            "ir.actions.report",
        ]

    def test_required_external_ids_exist(self):
        required = [
            "smart_construction_core.group_sc_super_admin",
            "smart_construction_core.menu_sc_root",
        ]
        missing = []
        for xid in required:
            if not self.env.ref(xid, raise_if_not_found=False):
                missing.append(xid)
        self.assertFalse(missing, "缺少必备 xmlid：%s" % ", ".join(missing))

    def test_actions_have_groups_at_install(self):
        action_imd = self.imd.search(
            [("module", "=", self.module), ("model", "in", self.action_models)]
        )
        missing = []
        for item in action_imd:
            act = self.env[item.model].browse(item.res_id).exists()
            if act and hasattr(act, "groups_id") and not act.groups_id:
                missing.append(item.complete_name or f"{item.module}.{item.name}")
        self.assertFalse(missing, "Action 缺少 groups_id：%s" % ", ".join(missing))

    def test_menu_action_bypass_at_install(self):
        menu_imd = self.imd.search(
            [("module", "=", self.module), ("model", "=", "ir.ui.menu")]
        )
        risky = []
        for item in menu_imd:
            menu = self.env["ir.ui.menu"].browse(item.res_id).exists()
            if not menu or not menu.action:
                continue
            act = menu.action
            if hasattr(act, "groups_id") and not act.groups_id:
                menu_xmlid = menu.get_external_id().get(menu.id) or item.complete_name
                act_xmlid = act.get_external_id().get(act.id) or ""
                risky.append(f"{menu_xmlid} -> {act_xmlid}")
        self.assertFalse(
            risky,
            "存在菜单有限流但 Action 无 groups 的绕过风险：%s" % ", ".join(risky),
        )
