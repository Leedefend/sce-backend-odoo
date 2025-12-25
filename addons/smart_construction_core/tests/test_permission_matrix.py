# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase, tagged

from .perm_matrix import PERM_MATRIX

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install", "sc_perm", "sc_upgrade")
class TestPermissionMatrix(TransactionCase):
    """L2 权限矩阵：角色-入口-动作的允许/拒绝应与矩阵一致。"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")

        def _create(login, group_xmlids):
            groups = [(6, 0, [cls.env.ref(x).id for x in group_xmlids])]
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "email": f"{login}@example.com",
                    "company_id": company.id,
                    "company_ids": [(6, 0, [company.id])],
                    "groups_id": groups,
                }
            )

        cls.users = {}
        for role, cfg in PERM_MATRIX.items():
            cls.users[role] = _create(role, cfg["groups"])

    def _action_allowed(self, user, action_xmlid):
        action = self.env.ref(action_xmlid)
        if not hasattr(action, "groups_id") or not action.groups_id:
            return True
        return bool(action.groups_id & user.groups_id)

    def _menu_visible(self, user, menu_xmlid):
        menu = self.env.ref(menu_xmlid)
        if not menu.groups_id:
            return True
        return bool(menu.groups_id & user.groups_id)

    def test_permission_matrix(self):
        failures = []
        for role, cfg in PERM_MATRIX.items():
            user = self.users[role]
            for action_xmlid in cfg.get("actions_allow", []):
                if not self._action_allowed(user, action_xmlid):
                    failures.append(f"{role} should ALLOW action {action_xmlid}")
            for action_xmlid in cfg.get("actions_deny", []):
                if self._action_allowed(user, action_xmlid):
                    failures.append(f"{role} should DENY action {action_xmlid}")
            for menu_xmlid in cfg.get("menus_allow", []):
                if not self._menu_visible(user, menu_xmlid):
                    failures.append(f"{role} should SEE menu {menu_xmlid}")
            for menu_xmlid in cfg.get("menus_deny", []):
                if self._menu_visible(user, menu_xmlid):
                    failures.append(f"{role} should NOT SEE menu {menu_xmlid}")
        if failures:
            _logger.info("Permission matrix failures: %s", failures)
        self.assertFalse(failures, "权限矩阵不匹配: %s" % "; ".join(failures))
