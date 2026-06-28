# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "runtime_user_management")
class TestRuntimeUserManagement(TransactionCase):
    def _create_user_with_profile(self, login, name, source_login=None, legacy_user_id=None):
        user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "login": login,
                "name": name,
                "email": "%s@example.test" % login,
            }
        )
        if "sc.legacy.user.profile" in self.env:
            self.env["sc.legacy.user.profile"].sudo().create(
                {
                    "legacy_user_id": legacy_user_id or login,
                    "source_login": source_login or login,
                    "display_name": name,
                    "user_id": user.id,
                }
            )
        return user

    def test_active_legacy_login_counts_as_runtime_company_user(self):
        user = self._create_user_with_profile("legacy_runtime_user_scope", "正式历史用户")

        users = self.env["res.users"].search([("sc_runtime_company_real_user", "=", True)])

        self.assertIn(user, users)

    def test_test_named_legacy_login_is_excluded_from_runtime_company_user(self):
        user = self._create_user_with_profile("legacy_runtime_test_scope", "测试历史用户")

        users = self.env["res.users"].search([("sc_runtime_company_real_user", "=", True)])

        self.assertNotIn(user, users)

    def test_runtime_source_login_uses_legacy_original_username(self):
        user = self._create_user_with_profile(
            "legacy_runtime_display_scope",
            "正式历史用户",
            source_login="runtime_original_user",
            legacy_user_id="runtime_legacy_001",
        )

        self.assertEqual(user.sc_runtime_source_login, "runtime_original_user")
        self.assertEqual(user.sc_runtime_legacy_user_id, "runtime_legacy_001")

    def test_runtime_source_login_is_searchable(self):
        user = self._create_user_with_profile(
            "legacy_runtime_search_scope",
            "正式历史用户",
            source_login="runtime_search_original",
            legacy_user_id="runtime_legacy_002",
        )

        users = self.env["res.users"].search([("sc_runtime_source_login", "ilike", "search_original")])

        self.assertIn(user, users)
