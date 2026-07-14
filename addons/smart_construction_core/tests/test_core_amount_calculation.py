# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_regression", "core_amount")
class TestCoreAmountCalculation(TransactionCase):
    """Focused evidence for core amount, tax, settlement, and payment balances."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.currency = cls.company.currency_id
        cls.project = cls.env["project.project"].create({"name": "Core Amount Project"})
        cls.partner = cls.env["res.partner"].create({"name": "Core Amount Partner"})
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.wbs = cls.env["construction.work.breakdown"].create(
            {
                "name": "Core Amount WBS",
                "code": "CORE-AMOUNT",
                "project_id": cls.project.id,
            }
        )
        cls.tax_purchase_9 = cls._create_percent_tax("Core Amount Purchase VAT 9%", 9.0, "purchase")
        cls.budget = cls.env["project.budget"].create(
            {
                "name": "Core Amount Budget",
                "project_id": cls.project.id,
            }
        )
        cls.boq_line_1 = cls._create_boq_line("Core Amount BOQ 1")
        cls.boq_line_2 = cls._create_boq_line("Core Amount BOQ 2")

    @classmethod
    def _create_percent_tax(cls, name, amount, tax_use):
        country = cls.env.ref("base.cn", raise_if_not_found=False)
        tax_group = cls.env["account.tax.group"].search(
            [("name", "=", "Core Amount VAT"), ("company_id", "=", cls.company.id)],
            limit=1,
        )
        if not tax_group:
            vals = {
                "name": "Core Amount VAT",
                "sequence": 10,
                "company_id": cls.company.id,
            }
            if country:
                vals["country_id"] = country.id
            tax_group = cls.env["account.tax.group"].create(vals)
        vals = {
            "name": name,
            "amount": amount,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "tax_group_id": tax_group.id,
            "company_id": cls.company.id,
            "active": True,
        }
        if country:
            vals["country_id"] = country.id
        return cls.env["account.tax"].create(vals)

    @classmethod
    def _create_boq_line(cls, name):
        return cls.env["project.budget.boq.line"].create(
            {
                "budget_id": cls.budget.id,
                "name": name,
                "wbs_id": cls.wbs.id,
                "uom_id": cls.uom_unit.id,
            }
        )

    def _create_contract(self):
        return self.env["construction.contract"].create(
            {
                "type": "in",
                "subject": "Core Amount Contract",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "tax_id": self.tax_purchase_9.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_1.id,
                            "qty_contract": 3,
                            "price_contract": 100.25,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_2.id,
                            "qty_contract": 2,
                            "price_contract": 49.50,
                        },
                    ),
                ],
            }
        )

    def _create_settlement(self, contract=None):
        return self.env["sc.settlement.order"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": (contract or self._create_contract()).id,
                "line_ids": [
                    (0, 0, {"name": "Core Amount Settlement A", "qty": 2, "price_unit": 120.25}),
                    (0, 0, {"name": "Core Amount Settlement B", "qty": 3, "price_unit": 19.90}),
                ],
            }
        )

    def _mark_payment_approved(self, payment):
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", payment.id),
        )
        self.env.invalidate_all()
        return self.env["payment.request"].browse(payment.id)

    def _assert_money(self, actual, expected):
        self.assertAlmostEqual(actual, expected, places=2)

    def test_contract_amounts_round_tax_from_line_total(self):
        contract = self._create_contract()

        self._assert_money(contract.line_ids[0].amount_contract, 300.75)
        self._assert_money(contract.line_ids[1].amount_contract, 99.0)
        self._assert_money(contract.line_amount_total, 399.75)
        self._assert_money(contract.amount_untaxed, 399.75)
        self._assert_money(contract.amount_tax, self.currency.round(399.75 * 0.09))
        self._assert_money(contract.amount_total, self.currency.round(399.75 + contract.amount_tax))

    def test_settlement_total_paid_and_payable_follow_approved_payment_amounts(self):
        contract = self._create_contract()
        settlement = self._create_settlement(contract=contract)

        self._assert_money(settlement.line_ids[0].amount, 240.50)
        self._assert_money(settlement.line_ids[1].amount, 59.70)
        self._assert_money(settlement.amount_total, 300.20)
        self._assert_money(settlement.paid_amount, 0.0)
        self._assert_money(settlement.remaining_amount, 300.20)
        self._assert_money(settlement.amount_payable, 300.20)

        payment = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 125.10,
                "type": "pay",
            }
        )
        payment = self._mark_payment_approved(payment)
        settlement.invalidate_recordset()
        payment.invalidate_recordset()

        self._assert_money(settlement.paid_amount, 125.10)
        self._assert_money(settlement.remaining_amount, 175.10)
        self._assert_money(settlement.amount_payable, 175.10)
        self._assert_money(payment.paid_amount_total, 0.0)
        self._assert_money(payment.unpaid_amount, 125.10)
        self.assertFalse(payment.is_fully_paid)

    def test_payment_uppercase_and_overpay_risk_use_current_payable_balance(self):
        contract = self._create_contract()
        settlement = self._create_settlement(contract=contract)
        paid = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 280.20,
                "type": "pay",
            }
        )
        paid = self._mark_payment_approved(paid)
        overpay = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 20.01,
                "type": "pay",
            }
        )
        settlement.invalidate_recordset()
        paid.invalidate_recordset()
        overpay.invalidate_recordset()

        self._assert_money(settlement.amount_payable, 20.0)
        self.assertEqual(paid.amount_uppercase, "贰佰捌拾元贰角")
        self.assertEqual(overpay.amount_uppercase, "贰拾元壹分")
        self.assertTrue(overpay.is_overpay_risk)
