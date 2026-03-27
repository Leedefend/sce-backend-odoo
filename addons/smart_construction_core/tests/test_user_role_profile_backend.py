# -*- coding: utf-8 -*-

from odoo.addons.smart_core.handlers.api_data import ApiDataHandler
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.identity.identity_resolver import IdentityResolver
from odoo.tests.common import TransactionCase, tagged


@tagged("sc_smoke", "sprint1_user_role_backend")
class TestUserRoleProfileBackend(TransactionCase):
    def _unwrap_handler_result(self, result):
        if isinstance(result, tuple):
            return result[0]
        return result

    def test_api_data_create_syncs_password_company_scope_and_role_groups(self):
        company = self.env.company
        handler = ApiDataHandler(self.env, payload={})

        result = handler.handle(
            params={
                "op": "create",
                "model": "res.users",
                "vals": {
                    "name": "Sprint1 API User",
                    "login": "sprint1-api-user@example.com",
                    "password": "Pass1234",
                    "company_id": company.id,
                    "sc_role_profile": "executive",
                    "active": True,
                },
            }
        )

        result = self._unwrap_handler_result(result)
        self.assertTrue(result.get("ok"), result)
        user_id = int((result.get("data") or {}).get("id") or 0)
        user = self.env["res.users"].sudo().browse(user_id)
        self.assertTrue(user.exists())
        self.assertEqual(user.company_id, company)
        self.assertIn(company, user.company_ids)
        self.assertEqual(user.sc_role_effective, "executive")
        self.assertIn("smart_construction_core.group_sc_super_admin", IdentityResolver(self.env).user_group_xmlids(user))
        self.assertEqual(
            self.env["res.users"].sudo().authenticate(self.env.cr.dbname, user.login, "Pass1234", {}),
            user.id,
        )

    def test_api_data_write_syncs_password_company_scope_and_role_groups(self):
        company = self.env.company
        other_company = self.env["res.company"].sudo().create({"name": "Sprint1 Other Company"})
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 API Update",
                "login": "sprint1-api-update@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "owner",
            }
        )
        handler = ApiDataHandler(self.env, payload={})

        result = handler.handle(
            params={
                "op": "write",
                "model": "res.users",
                "ids": [user.id],
                "vals": {
                    "company_id": other_company.id,
                    "password": "Pass5678",
                    "sc_role_profile": "executive",
                },
            }
        )

        result = self._unwrap_handler_result(result)
        self.assertTrue(result.get("ok"), result)
        user.invalidate_recordset()
        self.assertEqual(user.company_id, other_company)
        self.assertIn(other_company, user.company_ids)
        self.assertEqual(user.sc_role_effective, "executive")
        self.assertIn("smart_construction_core.group_sc_super_admin", IdentityResolver(self.env).user_group_xmlids(user))
        self.assertEqual(
            self.env["res.users"].sudo().authenticate(self.env.cr.dbname, user.login, "Pass5678", {}),
            user.id,
        )

    def test_user_action_open_contract_includes_role_profile_fields(self):
        action = self.env.ref("smart_enterprise_base.action_enterprise_user")
        handler = UiContractHandler(self.env)
        result = handler.handle(
            payload={
                "params": {
                    "op": "action_open",
                    "action_id": int(action.id),
                    "render_profile": "create",
                }
            }
        )

        self.assertTrue(result.get("ok"), result)
        data = result.get("data") or {}
        form_view = ((data.get("views") or {}).get("form") or {})
        layout = form_view.get("layout") or []
        field_names = set()
        field_strings = {}

        def collect_fields(nodes):
            for node in nodes or []:
                if not isinstance(node, dict):
                    continue
                if node.get("type") == "field" and node.get("name"):
                    name = str(node.get("name"))
                    field_names.add(name)
                    field_strings[name] = str(node.get("string") or "")
                collect_fields(node.get("children") or [])

        collect_fields(layout)

        self.assertIn("password", field_names)
        self.assertIn("sc_role_profile", field_names)
        self.assertIn("sc_role_effective", field_names)
        self.assertIn("sc_role_landing_label", field_names)
        self.assertEqual(field_strings.get("name"), "姓名")
        self.assertEqual(field_strings.get("password"), "初始密码")
        self.assertEqual(field_strings.get("sc_role_profile"), "产品角色")
        field_policies = data.get("field_policies") or {}
        role_profile_policy = field_policies.get("sc_role_profile") or {}
        role_effective_policy = field_policies.get("sc_role_effective") or {}
        self.assertIn("create", role_profile_policy.get("visible_profiles") or [])
        self.assertIn("create", role_effective_policy.get("readonly_profiles") or [])
        self.assertEqual(role_profile_policy.get("group"), "secondary")

    def test_role_profile_syncs_pm_groups_and_role_surface(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 PM",
                "login": "sprint1-pm@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "pm",
            }
        )

        resolver = IdentityResolver(self.env)
        role_code = resolver.resolve_role_code(resolver.user_group_xmlids(user))

        self.assertEqual(user.sc_role_profile, "pm")
        self.assertEqual(role_code, "pm")
        self.assertIn("smart_construction_core.group_sc_cap_project_manager", resolver.user_group_xmlids(user))

    def test_create_with_company_id_adds_allowed_company_scope(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 Executive",
                "login": "sprint1-executive@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "sc_role_profile": "executive",
            }
        )

        self.assertEqual(user.company_id, company)
        self.assertIn(company, user.company_ids)

    def test_role_profile_syncs_finance_groups_and_role_surface(self):
        company = self.env.company
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Sprint1 Finance",
                "login": "sprint1-finance@example.com",
                "password": "Pass1234",
                "company_id": company.id,
                "company_ids": [(6, 0, [company.id])],
                "sc_role_profile": "finance",
            }
        )

        resolver = IdentityResolver(self.env)
        role_code = resolver.resolve_role_code(resolver.user_group_xmlids(user))

        self.assertEqual(user.sc_role_profile, "finance")
        self.assertEqual(role_code, "finance")
        self.assertTrue(
            {
                "smart_construction_custom.group_sc_role_finance",
                "smart_construction_core.group_sc_cap_finance_manager",
            }
            & resolver.user_group_xmlids(user)
        )
