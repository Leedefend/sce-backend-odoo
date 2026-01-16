# -*- coding: utf-8 -*-
import csv
import logging
import os

from odoo.tests.common import TransactionCase, tagged

from .perm_matrix import PERM_MATRIX

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install", "sc_perm", "sc_upgrade")
class TestSidebarMenuVisibilityAudit(TransactionCase):
    """Audit sidebar menu visibility by role and emit a CSV report."""

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

    def _audit_path(self):
        repo_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, os.pardir)
        )
        docs_dir = os.path.join(repo_root, "docs", "audit")
        if os.path.isdir(docs_dir):
            probe = os.path.join(docs_dir, ".write_test")
            try:
                with open(probe, "w", encoding="utf-8") as handle:
                    handle.write("ok")
                os.unlink(probe)
                return os.path.join(docs_dir, "sidebar_menu_visibility.csv")
            except OSError:
                pass
        return "/tmp/sidebar_menu_visibility.csv"

    def _menu_visible(self, user, menu):
        if not menu:
            return False
        if not menu.groups_id:
            return True
        return bool(menu.groups_id & user.groups_id)

    def test_sidebar_menu_visibility_audit(self):
        menu_xmlids = sorted(
            {
                xmlid
                for cfg in PERM_MATRIX.values()
                for xmlid in cfg.get("menus_allow", []) + cfg.get("menus_deny", [])
            }
        )
        rows = []
        missing = []
        for menu_xmlid in menu_xmlids:
            menu = self.env.ref(menu_xmlid, raise_if_not_found=False)
            if not menu:
                missing.append(menu_xmlid)
            for role, user in self.users.items():
                rows.append(
                    {
                        "role": role,
                        "menu_xmlid": menu_xmlid,
                        "visible": self._menu_visible(user, menu),
                        "missing": not bool(menu),
                    }
                )

        target = self._audit_path()
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["role", "menu_xmlid", "visible", "missing"],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

        if missing:
            _logger.info("Sidebar menu audit missing xmlids: %s", ", ".join(missing))
        _logger.info("Sidebar menu visibility audit written to %s", target)
