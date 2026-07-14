from unittest import TestCase

from odoo.addons.smart_construction_core.core_extension_actor_roles import resolve_release_actor_role_codes
from odoo.addons.smart_core.delivery.menu_service import MenuService


class TestProjectMemberRoleSurface(TestCase):
    def test_project_read_capability_preserves_project_manager_actor_role(self):
        class User:
            groups_id = type("Groups", (), {"get_external_id": lambda self: {1: "base.group_user"}})()

            def has_group(self, xmlid):
                return xmlid == "smart_construction_core.group_sc_cap_project_read"

        self.assertEqual(resolve_release_actor_role_codes(User()), ["pm"])

    def test_project_member_menu_blocklist_is_semantic(self):
        self.assertFalse(MenuService._project_member_menu_allowed({"label": "支付申请", "menu_xmlid": "x"}))
        self.assertFalse(MenuService._project_member_menu_allowed({"label": "Project finance", "menu_xmlid": "x"}))
        self.assertTrue(MenuService._project_member_menu_allowed({"label": "项目台账", "menu_xmlid": "smart_construction_core.menu_sc_project_project"}))
