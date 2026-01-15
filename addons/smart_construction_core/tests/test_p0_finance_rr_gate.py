# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate")
class TestP0FinanceRrGate(TransactionCase):
    """P0 gate for finance domain RR scope (payment.request, settlement.order)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.ref("base.main_company")
        ctx = dict(
            cls.env.context,
            mail_create_nosubscribe=True,
            mail_notify_noemail=True,
            mail_auto_subscribe_no_notify=True,
            tracking_disable=True,
        )

        def _ctx(model):
            return cls.env[model].with_context(ctx)

        def _create_user(login, group_xmlids):
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

        cls.user_finance_read = _create_user(
            "p0_fin_rr_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )
        cls.user_finance_user = _create_user(
            "p0_fin_rr_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_finance_manager = _create_user(
            "p0_fin_rr_manager",
            ["smart_construction_core.group_sc_cap_finance_manager"],
        )
        cls.user_no_access = _create_user(
            "p0_fin_rr_none",
            ["base.group_user"],
        )

        cls.project_same = _ctx("project.project").create(
            {
                "name": "P0 Finance Project Same",
                "privacy_visibility": "followers",
                "user_id": cls.user_finance_user.id,
            }
        )
        cls.project_same.message_subscribe(
            partner_ids=[
                cls.user_finance_user.partner_id.id,
                cls.user_finance_read.partner_id.id,
            ]
        )
        cls.project_other = _ctx("project.project").create(
            {
                "name": "P0 Finance Project Other",
                "privacy_visibility": "followers",
                "user_id": cls.user_no_access.id,
            }
        )

        cls.partner = _ctx("res.partner").create({"name": "P0 Finance Partner"})
        cls.partner_other = _ctx("res.partner").create({"name": "P0 Finance Partner Other"})

        cls.settlement_same = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "line_ids": [(0, 0, {"name": "P0 Finance Line", "amount": 120.0})],
            }
        )
        cls.settlement_other = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner_other.id,
                "line_ids": [(0, 0, {"name": "P0 Finance Line Other", "amount": 80.0})],
            }
        )

        cls.payment_same = _ctx("payment.request").create(
            {
                "project_id": cls.project_same.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_same.id,
                "amount": 120.0,
                "type": "pay",
            }
        )
        cls.payment_other = _ctx("payment.request").create(
            {
                "project_id": cls.project_other.id,
                "partner_id": cls.partner_other.id,
                "settlement_id": cls.settlement_other.id,
                "amount": 80.0,
                "type": "pay",
            }
        )

    def _project_ids_from_groups(self, groups):
        return {g.get("project_id")[0] for g in groups if g.get("project_id")}

    def test_payment_request_read_group_scope_finance_read(self):
        groups = (
            self.env["payment.request"]
            .with_user(self.user_finance_read)
            .read_group([], ["id:count"], ["project_id"])
        )
        project_ids = self._project_ids_from_groups(groups)
        self.assertEqual(project_ids, {self.project_same.id})

    def test_payment_request_read_group_scope_finance_manager(self):
        groups = (
            self.env["payment.request"]
            .with_user(self.user_finance_manager)
            .read_group([], ["id:count"], ["project_id"])
        )
        project_ids = self._project_ids_from_groups(groups)
        self.assertTrue({self.project_same.id, self.project_other.id}.issubset(project_ids))

    def test_payment_request_read_group_denied_non_finance(self):
        with self.assertRaises(AccessError):
            self.env["payment.request"].with_user(self.user_no_access).read_group(
                [], ["id:count"], ["project_id"]
            )

    def test_settlement_read_group_scope_finance_read(self):
        groups = (
            self.env["sc.settlement.order"]
            .with_user(self.user_finance_read)
            .read_group([], ["id:count"], ["project_id"])
        )
        project_ids = self._project_ids_from_groups(groups)
        self.assertEqual(project_ids, {self.project_same.id})

    def test_settlement_read_group_scope_finance_manager(self):
        groups = (
            self.env["sc.settlement.order"]
            .with_user(self.user_finance_manager)
            .read_group([], ["id:count"], ["project_id"])
        )
        project_ids = self._project_ids_from_groups(groups)
        self.assertTrue({self.project_same.id, self.project_other.id}.issubset(project_ids))

    def test_settlement_read_group_denied_non_finance(self):
        with self.assertRaises(AccessError):
            self.env["sc.settlement.order"].with_user(self.user_no_access).read_group(
                [], ["id:count"], ["project_id"]
            )
