from odoo.tests import tagged
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


@tagged("post_install", "-at_install", "user_data_boundary")
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

    def test_formal_role_surface_uses_authoritative_product_label_and_home(self):
        resolver = self._resolver()
        matrix = {
            "finance": ({"smart_construction_custom.group_sc_role_finance"}, "财务主管"),
            "project_member": ({"smart_construction_core.group_sc_cap_project_read"}, "项目成员"),
            "pm": ({"smart_construction_custom.group_sc_role_pm"}, "项目经理"),
            "owner": ({"smart_construction_custom.group_sc_role_owner"}, "企业负责人"),
        }
        for role, (groups, label) in matrix.items():
            with self.subTest(role=role):
                surface = resolver.build_role_surface(
                    groups,
                    [],
                    {"projects.list", "projects.ledger"},
                    ROLE_SURFACE_OVERRIDES,
                )
                self.assertEqual(surface["role_code"], role)
                self.assertEqual(surface["role_label"], label)
                self.assertEqual(surface["landing_scene_key"], "workspace.home")
                self.assertEqual(surface["landing_path"], "/s/workspace.home")

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

    def test_restricted_role_has_no_release_or_delivery_navigation(self):
        resolver = self._resolver()
        surface = resolver.build_role_surface(set(), [], {"workspace.home"}, ROLE_SURFACE_OVERRIDES)
        nodes = [{"xmlid": "x.sensitive", "meta": {"model": "payment.request"}, "children": []}]

        self.assertEqual(surface["role_code"], "restricted")
        self.assertTrue(surface["deny_all_navigation"])
        self.assertEqual(resolver.filter_nav_for_role_surface(nodes, surface), [])
        self.assertEqual(MenuService._filter_role_surface_nodes(nodes, surface), [])

    def test_known_unreachable_actions_are_removed_by_stable_identifiers(self):
        resolver = self._resolver()
        nodes = [{
            "xmlid": "smart_construction_core.menu_sc_project_center",
            "children": [
                {
                    "xmlid": "smart_construction_core.menu_sc_plan",
                    "meta": {"action_xmlid": "smart_construction_core.action_sc_plan", "model": "sc.plan", "action_id": 1},
                },
                {
                    "xmlid": "smart_construction_core.menu_sc_plan_report",
                    "meta": {"action_xmlid": "smart_construction_core.action_sc_plan_report", "model": "sc.plan.report", "action_id": 2},
                },
                {
                    "xmlid": "smart_construction_core.menu_sc_tender_registration",
                    "meta": {"action_xmlid": "smart_construction_core.action_sc_tender_registration", "model": "tender.bid", "action_id": 3},
                },
                {
                    "xmlid": "smart_construction_core.menu_payment_request",
                    "meta": {"action_xmlid": "smart_construction_core.action_payment_request", "model": "payment.request", "action_id": 4},
                },
            ],
        }]
        forbidden_actions = {
            "finance": {
                "smart_construction_core.action_sc_plan",
                "smart_construction_core.action_sc_plan_report",
            },
            "project_member": {"smart_construction_core.action_sc_tender_registration"},
            "owner": {"smart_construction_core.action_sc_tender_registration"},
            "pm": set(),
        }
        role_groups = {
            "finance": {"smart_construction_custom.group_sc_role_finance"},
            "project_member": {"smart_construction_core.group_sc_cap_project_read"},
            "owner": {"smart_construction_custom.group_sc_role_owner"},
            "pm": {"smart_construction_custom.group_sc_role_pm"},
        }
        for role, groups in role_groups.items():
            with self.subTest(role=role):
                surface = resolver.build_role_surface(groups, [], {"projects.list"}, ROLE_SURFACE_OVERRIDES)
                for nav in (
                    resolver.filter_nav_for_role_surface(nodes, surface),
                    MenuService._filter_role_surface_nodes(nodes, surface),
                ):
                    actual = {child["meta"]["action_xmlid"] for child in nav[0]["children"]}
                    self.assertFalse(actual & forbidden_actions[role])
                    if role == "finance":
                        self.assertIn("smart_construction_core.action_payment_request", actual)
                    if role == "pm":
                        self.assertIn("smart_construction_core.action_sc_plan", actual)
                        self.assertIn("smart_construction_core.action_sc_plan_report", actual)
                        self.assertIn("smart_construction_core.action_sc_tender_registration", actual)
