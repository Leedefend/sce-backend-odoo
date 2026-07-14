# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged

from ..models.support import operating_metrics as opm


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

        tax = cls.env["account.tax"].search(
            [
                ("type_tax_use", "=", "purchase"),
                ("amount_type", "=", "percent"),
                ("price_include", "=", False),
            ],
            limit=1,
        )
        if not tax:
            tax = _ctx("account.tax").create(
                {
                    "name": "P0 Ledger Tax",
                    "amount": 0.0,
                    "amount_type": "percent",
                    "type_tax_use": "purchase",
                    "price_include": False,
                }
            )

        def _create_contract(name, project, partner):
            return _ctx("construction.contract").create(
                {
                    "subject": name,
                    "type": "in",
                    "project_id": project.id,
                    "partner_id": partner.id,
                    "tax_id": tax.id,
                }
            )

        cls.contract_main = _create_contract(
            "P0 Ledger Contract", cls.project, cls.partner
        )
        cls.settlement_ok = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_main.id,
                "line_ids": [(0, 0, {"name": "P0 Ledger Line", "amount": 100.0})],
            }
        )
        cls.settlement_ok.write({"state": "approve"})

        cls.settlement_draft = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_main.id,
                "line_ids": [(0, 0, {"name": "P0 Ledger Line Draft", "amount": 100.0})],
            }
        )

        cls.payment_ok = _ctx("payment.request").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_main.id,
                "settlement_id": cls.settlement_ok.id,
                "amount": 100.0,
                "type": "pay",
            }
        )
        cls.payment_bad_settlement = _ctx("payment.request").create(
            {
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
                "contract_id": cls.contract_main.id,
                "settlement_id": cls.settlement_draft.id,
                "amount": 100.0,
                "type": "pay",
            }
        )

        cls.other_project = _ctx("project.project").create(
            {
                "name": "P0 Ledger Project Other",
                "privacy_visibility": "followers",
                "user_id": cls.user_no_access.id,
            }
        )
        cls.other_partner = _ctx("res.partner").create({"name": "P0 Ledger Partner Other"})
        cls.contract_other = _create_contract("P0 Ledger Contract Other", cls.other_project, cls.other_partner)
        cls.other_settlement = _ctx("sc.settlement.order").create(
            {
                "project_id": cls.other_project.id,
                "partner_id": cls.other_partner.id,
                "contract_id": cls.contract_other.id,
                "line_ids": [(0, 0, {"name": "P0 Ledger Line Other", "amount": 80.0})],
            }
        )
        cls.other_settlement.write({"state": "approve"})
        cls.other_payment = _ctx("payment.request").create(
            {
                "project_id": cls.other_project.id,
                "partner_id": cls.other_partner.id,
                "contract_id": cls.contract_other.id,
                "settlement_id": cls.other_settlement.id,
                "amount": 80.0,
                "type": "pay",
            }
        )

        cls.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id in %s",
            (
                "approved",
                "validated",
                (cls.payment_ok.id, cls.payment_bad_settlement.id, cls.other_payment.id),
            ),
        )
        cls.env.invalidate_all()
        cls.other_ledger = cls.other_payment.sudo()._ensure_payment_ledger()
        cls.treasury_same = (
            _ctx("sc.treasury.ledger")
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": cls.project.id,
                    "partner_id": cls.partner.id,
                    "settlement_id": cls.settlement_ok.id,
                    "payment_request_id": cls.payment_ok.id,
                    "amount": 100.0,
                }
            )
        )
        cls.treasury_other = (
            _ctx("sc.treasury.ledger")
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": cls.other_project.id,
                    "partner_id": cls.other_partner.id,
                    "settlement_id": cls.other_settlement.id,
                    "payment_request_id": cls.other_payment.id,
                    "amount": 80.0,
                }
            )
        )

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

    def test_rr_ledger_read_scope_finance_read(self):
        ledger = self.payment_ok.with_user(self.user_finance_user)._ensure_payment_ledger()
        can_read = self.env["payment.ledger"].with_user(self.user_finance_read).search_count(
            [("id", "=", ledger.id)]
        )
        cannot_read = self.env["payment.ledger"].with_user(self.user_finance_read).search_count(
            [("id", "=", self.other_ledger.id)]
        )
        self.assertEqual(can_read, 1)
        self.assertEqual(cannot_read, 0)

    def test_rr_ledger_read_denied_non_finance(self):
        with self.assertRaises(AccessError):
            self.env["payment.ledger"].with_user(self.user_no_access).search_count([])

    def test_action_menu_groups_for_ledger(self):
        action = self.env.ref("smart_construction_core.action_payment_ledger")
        menu = self.env.ref("smart_construction_core.menu_payment_ledger")
        self.assertTrue(action.groups_id)
        self.assertTrue(menu.groups_id)

    def test_rr_treasury_read_scope_finance_read(self):
        can_read = self.env["sc.treasury.ledger"].with_user(self.user_finance_read).search_count(
            [("id", "=", self.treasury_same.id)]
        )
        cannot_read = self.env["sc.treasury.ledger"].with_user(self.user_finance_read).search_count(
            [("id", "=", self.treasury_other.id)]
        )
        self.assertEqual(can_read, 1)
        self.assertEqual(cannot_read, 0)

    def test_rr_treasury_read_denied_non_finance(self):
        with self.assertRaises(AccessError):
            self.env["sc.treasury.ledger"].with_user(self.user_no_access).search_count([])

    def test_action_menu_groups_for_treasury_ledger(self):
        action = self.env.ref("smart_construction_core.action_sc_treasury_ledger")
        menu = self.env.ref("smart_construction_core.menu_sc_treasury_ledger")
        group_ids = {
            self.env.ref("smart_construction_core.group_sc_cap_finance_read").id,
            self.env.ref("smart_construction_core.group_sc_cap_finance_user").id,
            self.env.ref("smart_construction_core.group_sc_cap_finance_manager").id,
        }
        self.assertTrue(group_ids.issubset(set(action.groups_id.ids)))
        self.assertTrue(group_ids.issubset(set(menu.groups_id.ids)))


@tagged("post_install", "-at_install", "sc_gate", "core_payment_amount_semantics")
class TestCorePaymentAmountSemantics(TransactionCase):
    """T1-B matrix: reservation, ledger actual paid, and contract actual paid."""

    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.currency = self.company.currency_id
        self.partner = self.env["res.partner"].create({"name": "T1-B Vendor"})
        self.project = self._project("T1-B Project", self.company)
        self.contract = self._contract(
            "T1-B Contract", self.project, self.partner, self.company, self.currency
        )
        self.settlement = self._settlement(
            "T1-B Settlement", self.project, self.partner, self.contract, self.company, self.currency
        )

    def _model(self, name, company=None):
        company = company or self.company
        company_ids = list(set(self.env.companies.ids + [self.company.id, company.id]))
        return self.env[name].sudo().with_context(allowed_company_ids=company_ids).with_company(company)

    def _project(self, name, company):
        return self._model("project.project", company).create(
            {"name": name, "company_id": company.id, "privacy_visibility": "followers"}
        )

    def _tax(self, name, company):
        group = self._model("account.tax.group", company).search(
            [("company_id", "=", company.id)], limit=1
        )
        if not group:
            group = self._model("account.tax.group", company).create(
                {"name": f"{company.name} Tax Group", "company_id": company.id}
            )
        return self._model("account.tax", company).create(
            {
                "name": name,
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "company_id": company.id,
                "tax_group_id": group.id,
                "country_id": (company.country_id or self.env.ref("base.cn")).id,
            }
        )

    def _contract(self, name, project, partner, company, currency):
        return self._model("construction.contract", company).create(
            {
                "subject": name,
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "company_id": company.id,
                "currency_id": currency.id,
                "tax_id": self._tax(f"{name} Tax", company).id,
            }
        )

    def _settlement(self, name, project, partner, contract, company, currency, amount=100.0):
        return self._model("sc.settlement.order", company).create(
            {
                "name": name,
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "company_id": company.id,
                "currency_id": currency.id,
                "settlement_type": "out",
                "state": "approve",
                "line_ids": [(0, 0, {"name": name, "qty": 1.0, "price_unit": amount})],
            }
        )

    def _request(
        self, name, amount, state="draft", settlement=None, project=None, contract=None, currency=None
    ):
        settlement = settlement or self.settlement
        project = project or settlement.project_id
        contract = contract if contract is not None else settlement.contract_id
        currency = currency or settlement.currency_id
        return self._model("payment.request", project.company_id).with_context(
            payment_soft_gate=True
        ).create(
            {
                "name": name,
                "type": "pay",
                "project_id": project.id,
                "partner_id": settlement.partner_id.id,
                "contract_id": contract.id if contract else False,
                "settlement_id": settlement.id,
                "currency_id": currency.id,
                "amount": amount,
                "state": state,
            }
        )

    def _contract_paid(self):
        self.contract.invalidate_recordset(["paid_amount"])
        return self.contract.paid_amount

    def test_settlement_adjusted_reservation_matrix(self):
        # 1. 100, no adjustment/request => 100 reservable.
        self.assertEqual(opm.settlement_remaining_reservable_amount(self.settlement), 100.0)
        adjustment = self._model("sc.settlement.adjustment").create(
            {
                "settlement_id": self.settlement.id,
                "adjustment_type": "deduction",
                "item_name": "T1-B Deduction",
                "amount": 10.0,
                "state": "confirmed",
            }
        )
        self.settlement.invalidate_recordset()
        # 2. Confirmed deduction immediately reduces capacity to 90.
        self.assertEqual(self.settlement.amount_payable, 90.0)
        adjustment.action_cancel()
        self.settlement.invalidate_recordset()
        # 3. Cancelling the deduction restores 100.
        self.assertEqual(self.settlement.amount_payable, 100.0)
        self._model("sc.settlement.adjustment").create(
            {
                "settlement_id": self.settlement.id,
                "adjustment_type": "deduction",
                "item_name": "T1-B Active Deduction",
                "amount": 10.0,
                "state": "confirmed",
            }
        )
        request_80 = self._request("T1-B PR 80", 80.0, "submit")
        self.settlement.invalidate_recordset()
        # 4. Submitted 80 leaves 10 after the confirmed deduction.
        self.assertEqual((self.settlement.paid_amount, self.settlement.amount_payable), (80.0, 10.0))
        request_80.with_context(allow_transition=True, payment_soft_gate=True).write({"state": "cancel"})
        self.settlement.invalidate_recordset()
        # 5. Cancelling the request releases capacity back to 90.
        self.assertEqual((self.settlement.paid_amount, self.settlement.amount_payable), (0.0, 90.0))
        active = self._request("T1-B PR 80 Active", 80.0, "submit")
        # 6. Editing excludes the active request itself.
        active._check_settlement_remaining_amount()
        # 7. A further 11 is rejected; 8. a further 10 is allowed.
        with self.assertRaises(UserError):
            self._request("T1-B PR 11", 11.0)._check_settlement_remaining_amount()
        self._request("T1-B PR 10", 10.0)._check_settlement_remaining_amount()

    def test_actual_paid_is_ledger_only_and_reverses(self):
        request = self._request("T1-B Actual PR", 80.0, "submit")
        # 9. Submitted request without ledger is not actual paid.
        self.assertEqual(opm.settlement_actual_paid_amount_map(self.env, [self.settlement.id]), {})
        request.flush_recordset(["state"])
        self.env.cr.execute("UPDATE payment_request SET state='approved' WHERE id=%s", (request.id,))
        request.invalidate_recordset(["state"])
        ledger = request._ensure_payment_ledger(amount=80.0)
        # 10. payment.ledger is the sole actual-paid fact.
        self.assertEqual(
            opm.settlement_actual_paid_amount_map(self.env, [self.settlement.id])[self.settlement.id],
            80.0,
        )
        execution = self._model("sc.payment.execution").create(
            {
                "name": "T1-B Paid Execution",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "payment_request_id": request.id,
                "currency_id": self.currency.id,
                "paid_amount": 80.0,
                "planned_amount": 80.0,
                "state": "paid",
            }
        )
        execution._reverse_paid_execution()
        request.invalidate_recordset()
        # 11. Reversal deletes ledger and actual paid returns to zero.
        self.assertFalse(ledger.exists())
        self.assertEqual(opm.settlement_actual_paid_amount_map(self.env, [self.settlement.id]), {})

    def test_contract_actual_paid_state_matrix(self):
        Execution = self._model("sc.payment.execution")
        common = {
            "project_id": self.project.id,
            "partner_id": self.partner.id,
            "contract_id": self.contract.id,
            "currency_id": self.currency.id,
        }
        Execution.create({**common, "name": "T1-B Draft", "paid_amount": 10.0, "state": "draft"})
        # 12. Draft and 13. confirmed are excluded.
        self.assertEqual(self._contract_paid(), 0.0)
        Execution.create({**common, "name": "T1-B Confirmed", "paid_amount": 20.0, "state": "confirmed"})
        self.assertEqual(self._contract_paid(), 0.0)
        paid = Execution.create({**common, "name": "T1-B Paid", "paid_amount": 30.0, "state": "paid"})
        # 14. Paid increases contract actual paid.
        self.assertEqual(self._contract_paid(), 30.0)
        paid.write({"state": "cancel"})
        self.assertEqual(self._contract_paid(), 0.0)
        paid.write({"state": "paid"})
        paid.flush_recordset(["state"])
        self.env.cr.execute("UPDATE sc_payment_execution SET state='cancelled' WHERE id=%s", (paid.id,))
        self.env.invalidate_all()
        # 15. cancel/cancelled are excluded.
        self.assertEqual(self._contract_paid(), 0.0)
        for number, amount in enumerate((10.0, 20.0, 30.0), 1):
            Execution.create({**common, "name": f"T1-B Paid {number}", "paid_amount": amount, "state": "paid"})
        # 16. Three paid executions accumulate.
        self.assertEqual(self._contract_paid(), 60.0)

    def test_project_company_and_currency_isolation(self):
        partner = self.env["res.partner"].create({"name": "T1-B Other Vendor"})
        project = self._project("T1-B Other Project", self.company)
        contract = self._contract("T1-B Other Contract", project, partner, self.company, self.currency)
        settlement = self._settlement(
            "T1-B Other Settlement", project, partner, contract, self.company, self.currency
        )
        self._request("T1-B Main Reserved", 30.0, "submit")
        self._request("T1-B Other Reserved", 40.0, "submit", settlement, project, contract)
        reserved = opm.settlement_reserved_amount_map(self.env, [self.settlement.id, settlement.id])
        # 17. Projects do not mix reservations.
        self.assertEqual((reserved[self.settlement.id], reserved[settlement.id]), (30.0, 40.0))
        company = self.env["res.company"].create(
            {
                "name": "T1-B Company 2",
                "currency_id": self.currency.id,
                "country_id": self.env.ref("base.cn").id,
            }
        )
        project_2 = self._project("T1-B Company 2 Project", company)
        partner_2 = self.env["res.partner"].create({"name": "T1-B Company 2 Vendor"})
        contract_2 = self._contract("T1-B Company 2 Contract", project_2, partner_2, company, self.currency)
        settlement_2 = self._settlement(
            "T1-B Company 2 Settlement", project_2, partner_2, contract_2, company, self.currency
        )
        self._request("T1-B Company 2 Reserved", 50.0, "submit", settlement_2, project_2, contract_2)
        reserved = opm.settlement_reserved_amount_map(self.env, [self.settlement.id, settlement_2.id])
        # 18. Companies do not mix reservations.
        self.assertEqual((reserved[self.settlement.id], reserved[settlement_2.id]), (30.0, 50.0))
        foreign = self.env["res.currency"].create(
            {"name": "XTB", "symbol": "XTB", "rounding": 0.01, "active": True}
        )
        with self.assertRaises(ValidationError):
            self._request("T1-B Request Currency Mismatch", 1.0, currency=foreign)
        legacy_mismatch = self._request("T1-B Legacy Currency Mismatch", 1.0)
        legacy_mismatch.flush_recordset(["currency_id"])
        self.env.cr.execute(
            "UPDATE payment_request SET currency_id=%s WHERE id=%s",
            (foreign.id, legacy_mismatch.id),
        )
        self.env.invalidate_all()
        self.assertTrue(legacy_mismatch.is_overpay_risk)
        foreign_contract = self._contract(
            "T1-B Foreign Contract", self.project, self.partner, self.company, foreign
        )
        foreign_settlement = self._settlement(
            "T1-B Foreign Contract Settlement",
            self.project,
            self.partner,
            foreign_contract,
            self.company,
            self.currency,
        )
        with self.assertRaises(ValidationError):
            self._request("T1-B Contract Currency Mismatch", 1.0, settlement=foreign_settlement)
        # 19. Missing conversion facts cause explicit rejection.

    def test_settlement_currency_rounding_boundaries(self):
        currency = self.env["res.currency"].create(
            {"name": "XTR", "symbol": "XTR", "rounding": 0.05, "active": True}
        )
        contract = self._contract("T1-B Rounding Contract", self.project, self.partner, self.company, currency)
        settlement = self._settlement(
            "T1-B Rounding Settlement", self.project, self.partner, contract, self.company, currency
        )
        self._request("T1-B Rounding Reserved", 80.0, "submit", settlement, contract=contract, currency=currency)
        below = self._request("T1-B Below Half", 20.024, settlement=settlement, contract=contract, currency=currency)
        above = self._request("T1-B Above Half", 20.026, settlement=settlement, contract=contract, currency=currency)
        # 20. Settlement currency half-unit boundary; 21. equality allowed.
        below._check_settlement_remaining_amount()
        with self.assertRaises(UserError):
            above._check_settlement_remaining_amount()
        self._request("T1-B Equal", 20.0, settlement=settlement, contract=contract, currency=currency)._check_settlement_remaining_amount()
        # 22. One minimum unit over is rejected.
        with self.assertRaises(UserError):
            self._request(
                "T1-B One Unit Over", 20.05, settlement=settlement, contract=contract, currency=currency
            )._check_settlement_remaining_amount()
        # 23. Less than rounding tolerance is not a false overpay.
        self.assertFalse(below.is_overpay_risk)
