from odoo.tests.common import TransactionCase

from odoo.addons.smart_construction_core.core_extension_actor_roles import resolve_release_actor_role_codes
from odoo.addons.smart_construction_core.core_extension_policy_maps import (
    ROLE_GROUPS_CAPABILITY_FALLBACK,
    ROLE_GROUPS_EXPLICIT,
    ROLE_PRECEDENCE,
    ROLE_SURFACE_OVERRIDES,
)
from odoo.addons.smart_core.delivery.menu_service import MenuService
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver


class TestProjectMemberRoleSurface(TransactionCase):
    def _resolver(self):
        resolver = IdentityResolver()
        resolver._role_groups_explicit = ROLE_GROUPS_EXPLICIT
        resolver._role_groups_capability_fallback = ROLE_GROUPS_CAPABILITY_FALLBACK
        resolver._role_precedence = ROLE_PRECEDENCE
        resolver._role_surface_map = {**resolver._role_surface_map, **ROLE_SURFACE_OVERRIDES}
        return resolver

    def test_role_matrix_uses_authoritative_groups(self):
        resolver = self._resolver()
        matrix = {
            "project_member": {"smart_construction_core.group_sc_cap_project_read"},
            "finance": {"smart_construction_custom.group_sc_role_finance"},
            "pm": {"smart_construction_custom.group_sc_role_pm", "smart_construction_core.group_sc_cap_project_read"},
            "owner": {"smart_construction_custom.group_sc_role_owner", "smart_construction_core.group_sc_cap_project_read"},
        }
        for expected, groups in matrix.items():
            with self.subTest(expected=expected):
                self.assertEqual(resolver.resolve_role_code(groups), expected)

    def test_release_actor_role_does_not_promote_project_reader_to_pm(self):
        class User:
            groups_id = type("Groups", (), {"get_external_id": lambda self: {1: "base.group_user"}})()

            def has_group(self, xmlid):
                return xmlid == "smart_construction_core.group_sc_cap_project_read"

        self.assertEqual(resolve_release_actor_role_codes(User()), ["project_member"])

    def test_release_and_delivery_navigation_use_identifier_policy(self):
        resolver = self._resolver()
        surface = resolver.build_role_surface(
            {"smart_construction_core.group_sc_cap_project_read"},
            [],
            {"projects.list"},
            ROLE_SURFACE_OVERRIDES,
        )
        nodes = [{
            "xmlid": "smart_construction_core.menu_sc_project_center",
            "children": [
                {"xmlid": "smart_construction_core.menu_sc_project_project", "meta": {"model": "project.project", "action_id": 1}},
                {"xmlid": "x.payment", "meta": {"model": "payment.request", "action_id": 2}},
                {"xmlid": "x.settlement", "meta": {"model": "sc.settlement.order", "action_id": 3}},
            ],
        }]
        release_nav = resolver.filter_nav_for_role_surface(nodes, surface)
        delivery_nav = MenuService._filter_role_surface_nodes(nodes, surface)
        for nav in (release_nav, delivery_nav):
            models = [child.get("meta", {}).get("model") for child in nav[0]["children"]]
            self.assertEqual(models, ["project.project"])

    def test_finance_navigation_is_not_affected_by_project_member_policy(self):
        nodes = [{"meta": {"model": "payment.request", "action_id": 2}, "children": []}]
        self.assertEqual(MenuService._filter_role_surface_nodes(nodes, {"role_code": "finance"}), nodes)
