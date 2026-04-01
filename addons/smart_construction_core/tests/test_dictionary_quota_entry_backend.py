# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "dictionary_quota_entry")
class TestDictionaryQuotaEntryBackend(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")

        def _create(login, role_profile):
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "sc_role_profile": role_profile,
                    "company_id": company.id,
                    "company_ids": [(6, 0, [company.id])],
                }
            )

        cls.pm_user = _create("dictionary_quota_pm", "pm")
        cls.finance_user = _create("dictionary_quota_finance", "finance")
        cls.executive_user = _create("dictionary_quota_executive", "executive")
        cls.business_admin_user = _create("dictionary_quota_business_admin", "business_admin")

    def test_quota_center_entry_server_action_returns_client_action_for_delivered_roles(self):
        action_ref = "smart_construction_core.action_project_quota_center_entry"

        for user in (
            self.pm_user,
            self.finance_user,
            self.executive_user,
            self.business_admin_user,
        ):
            action = self.env.ref(action_ref).with_user(user).run()

            self.assertEqual(action.get("type"), "ir.actions.client")
            self.assertEqual(action.get("tag"), "project_quota_center")
