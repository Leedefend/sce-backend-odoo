# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate")
class TestP0LedgerGate(TransactionCase):
    """P0 gate for ledger creation and enforcement."""

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

        cls.user_finance_user = _create_user(
            "p0_ledger_fin_user",
            ["smart_construction_core.group_sc_cap_finance_user"],
        )
        cls.user_finance_read = _create_user(
            "p0_ledger_fin_read",
            ["smart_construction_core.group_sc_cap_finance_read"],
        )
        cls.user_no_access = _create_user(
            "p0_ledger_no_access",
            ["base.group_user"],
        )

        cls.project = _ctx("project.project").create(
            {
                "name": "P0 Ledger Project",
                "privacy_visibility": "followers",
                "user_id": cls.user_finance_user.id,
            }
        )
        cls.project.message_subscribe(
            partner_ids=[
                cls.user_finance_user.partner_id.id,
                cls.user_finance_read.partner_id.id,
            ]
        )
        cls.partner = _ctx("res.partner").create({"name": "P0 Ledger Partner"})

        cls.settlement_ok = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "line_ids": [(0, 0, {"name": "P0 Ledger Line", "amount": 100.0})],
            }
        )
        cls.settlement_ok.write({"state": "approve"})

        cls.settlement_draft = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "line_ids": [(0, 0, {"name": "P0 Ledger Line Draft", "amount": 100.0})],
            }
        )

        cls.payment_ok = _ctx("payment.request").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_ok.id,
                "amount": 100.0,
                "type": "pay",
            }
        )
        cls.payment_bad_settlement = _ctx("payment.request").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "settlement_id": cls.settlement_draft.id,
                "amount": 100.0,
                "type": "pay",
            }
        )

        cls.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id in %s",
            ("approved", "validated", (cls.payment_ok.id, cls.payment_bad_settlement.id)),
        )
        cls.env.invalidate_all()

    def test_create_ledger_from_approved_payment(self):
        ledger = self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        self.assertEqual(ledger.payment_request_id.id, self.payment_ok.id)
        self.assertEqual(ledger.amount, self.payment_ok.amount)

    def test_ledger_idempotent_per_request(self):
        first = self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        second = self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        self.assertEqual(first.id, second.id)
        count = self.env["payment.ledger"].sudo().search_count(
            [("payment_request_id", "=", self.payment_ok.id)]
        )
        self.assertEqual(count, 1)

    def test_ledger_amount_matches_request(self):
        ledger = self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        self.assertEqual(ledger.amount, self.payment_ok.amount)

    def test_block_when_settlement_not_approved(self):
        with self.assertRaises(UserError):
            self.payment_bad_settlement.with_user(self.user_finance_user)._ensure_payment_ledger()

    def test_block_unauthorized_create(self):
        with self.assertRaises(AccessError):
            self.payment_ok.with_user(self.user_finance_read)._ensure_payment_ledger()

    def test_block_create_without_context(self):
        with self.assertRaises(UserError):
            self.env["payment.ledger"].with_user(self.user_finance_user).create(
                {
                    "payment_request_id": self.payment_ok.id,
                    "amount": self.payment_ok.amount,
                }
            )

    def test_block_duplicate_create(self):
        self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        with self.assertRaises(UserError):
            self.env["payment.ledger"].with_user(self.user_finance_user).with_context(
                allow_payment_ledger_create=True
            ).create(
                {
                    "payment_request_id": self.payment_ok.id,
                    "amount": self.payment_ok.amount,
                }
            )

    def test_block_overpay(self):
        with self.assertRaises(UserError):
            self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger(amount=1000.0)

    def test_ui_blocks_direct_ledger_create(self):
        tree_view = self.env.ref("smart_construction_core.view_payment_ledger_tree").arch_db
        form_view = self.env.ref("smart_construction_core.view_payment_ledger_form").arch_db
        self.assertIn('create="false"', tree_view)
        self.assertIn('edit="false"', tree_view)
        self.assertIn('delete="false"', tree_view)
        self.assertIn('create="false"', form_view)
        self.assertIn('edit="false"', form_view)
        self.assertIn('delete="false"', form_view)

    def test_ui_blocks_ledger_lines_inline_create(self):
        view = self.env.ref("smart_construction_core.view_payment_request_form").arch_db
        self.assertIn('name="ledger_line_ids"', view)
        self.assertIn('create="false"', view)
