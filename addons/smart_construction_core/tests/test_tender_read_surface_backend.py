# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "tender_read_surface")
class TestTenderReadSurfaceBackend(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")

        def _create(login, role_profile, extra_group_xmlids=None):
            groups = [(6, 0, [cls.env.ref(xmlid).id for xmlid in (extra_group_xmlids or [])])]
            return cls.env["res.users"].with_context(no_reset_password=True).create(
                {
                    "name": login,
                    "login": login,
                    "sc_role_profile": role_profile,
                    "company_id": company.id,
                    "company_ids": [(6, 0, [company.id])],
                    "groups_id": groups,
                }
            )

        cls.finance_user = _create(
            "tender_read_surface_finance",
            "finance",
        )
        cls.pm_user = _create(
            "tender_read_surface_pm",
            "pm",
        )
        cls.executive_user = _create(
            "tender_read_surface_executive",
            "executive",
        )
        cls.project = cls.env["project.project"].create({"name": "Tender Read Surface Project"})
        cls.tender = cls.env["tender.bid"].with_user(cls.pm_user).create(
            {
                "project_id": cls.project.id,
                "tender_name": "Tender Read Surface Bid",
            }
        )

    def test_finance_role_has_read_only_tender_acl(self):
        expected_models = [
            "tender.bid",
            "tender.bid.line",
            "tender.doc.purchase",
            "tender.survey",
            "tender.doc.review",
            "tender.opening",
            "tender.opening.competitor",
            "tender.guarantee",
        ]

        for model_name in expected_models:
            model = self.env[model_name].with_user(self.finance_user)
            self.assertTrue(model.check_access_rights("read", raise_exception=False), model_name)
            self.assertFalse(model.check_access_rights("create", raise_exception=False), model_name)
            self.assertFalse(model.check_access_rights("write", raise_exception=False), model_name)
            self.assertFalse(model.check_access_rights("unlink", raise_exception=False), model_name)

    def test_execution_roles_keep_tender_write_acl(self):
        for user in (self.pm_user, self.executive_user):
            model = self.env["tender.bid"].with_user(user)

            self.assertTrue(model.check_access_rights("read", raise_exception=False))
            self.assertTrue(model.check_access_rights("create", raise_exception=False))
            self.assertTrue(model.check_access_rights("write", raise_exception=False))
            self.assertTrue(model.check_access_rights("unlink", raise_exception=False))

    def test_tender_action_remains_visible_to_finance(self):
        action = (
            self.env.ref("smart_construction_core.action_tender_bid")
            .with_user(self.finance_user)
            .sudo(False)
            .read(["res_model"])[0]
        )

        self.assertEqual(action["res_model"], "tender.bid")
        self.assertTrue(self.tender.with_user(self.finance_user).exists())

    def test_finance_form_uses_non_clickable_statusbar(self):
        view = (
            self.env["tender.bid"]
            .with_user(self.finance_user)
            .get_view(
                self.env.ref("smart_construction_core.view_tender_bid_form").id,
                view_type="form",
            )
        )

        arch = etree.fromstring(view["arch"].encode())
        clickable = arch.xpath("//header/field[@name='state' and contains(@options, \"clickable\")]")
        readonly = arch.xpath("//header/field[@name='state' and @readonly='1']")

        self.assertFalse(clickable)
        self.assertTrue(readonly)

    def test_execution_forms_keep_clickable_statusbar(self):
        for user in (self.pm_user, self.executive_user):
            view = (
                self.env["tender.bid"]
                .with_user(user)
                .get_view(
                    self.env.ref("smart_construction_core.view_tender_bid_form").id,
                    view_type="form",
                )
            )

            arch = etree.fromstring(view["arch"].encode())
            clickable = arch.xpath("//header/field[@name='state' and contains(@options, \"clickable\")]")
            readonly = arch.xpath("//header/field[@name='state' and @readonly='1']")

            self.assertTrue(clickable)
            self.assertFalse(readonly)
