# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "sc_gate", "p0_state")
class TestP0StateClosure(TransactionCase):
    def setUp(self):
        super().setUp()
        self.company = self.env.ref("base.main_company")
        self.uom_unit = self.env.ref("uom.product_uom_unit")

    def _create_project(self, name, with_boq=False):
        owner = self._create_partner(f"{name} Owner")
        project = self.env["project.project"].create(
            {
                "name": name,
                "owner_id": owner.id,
                "manager_id": self.env.user.id,
                "location": "Test Location",
            }
        )
        if with_boq:
            self.env["project.boq.line"].create(
                {
                    "project_id": project.id,
                    "code": "BOQ-001",
                    "name": "BOQ Item",
                    "uom_id": self.uom_unit.id,
                    "quantity": 10.0,
                    "price": 1.0,
                }
            )
        return project

    def _create_partner(self, name="P0 Partner"):
        return self.env["res.partner"].create({"name": name})

    def _create_tax(self, name="P0 VAT 9%", tax_use="purchase"):
        return self.env["account.tax"].create(
            {
                "name": name,
                "amount": 9.0,
                "amount_type": "percent",
                "type_tax_use": tax_use,
                "price_include": False,
                "company_id": self.company.id,
            }
        )

    def _create_contract(self, project, partner):
        tax = self._create_tax()
        return self.env["construction.contract"].create(
            {
                "subject": "P0 Contract",
                "type": "in",
                "project_id": project.id,
                "partner_id": partner.id,
                "tax_id": tax.id,
            }
        )

    def _enable_funding(self, project, cap=1000.0):
        project.write({"funding_enabled": True})
        self.env["project.funding.baseline"].create(
            {"project_id": project.id, "total_amount": cap, "state": "active"}
        )

    def _create_settlement_order(self, project, partner, contract, amount=100.0, state="approve"):
        return self.env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_type": "out",
                "line_ids": [(0, 0, {"name": "P0 Line", "qty": 1.0, "price_unit": amount})],
                "state": state,
            }
        )

    def _create_settlement(self, project, partner, state="confirmed"):
        return self.env["project.settlement"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 100.0,
                "state": state,
            }
        )

    def test_project_lifecycle_requires_boq(self):
        project = self._create_project("P0 Project No BOQ")
        with self.assertRaises(UserError):
            project.action_set_lifecycle_state("in_progress")

        project = self._create_project("P0 Project With BOQ", with_boq=True)
        project.action_set_lifecycle_state("in_progress")
        self.assertEqual(project.lifecycle_state, "in_progress")

    def test_project_lifecycle_blocked_by_settlement(self):
        project = self._create_project("P0 Project Settlement", with_boq=True)
        partner = self._create_partner()
        self._create_settlement(project, partner, state="confirmed")
        with self.assertRaises(UserError):
            project.action_set_lifecycle_state("warranty")

    def test_project_lifecycle_blocked_by_payment(self):
        project = self._create_project("P0 Project Payment", with_boq=True)
        partner = self._create_partner("P0 Payee")
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "draft",
            }
        )
        # Avoid validator dependencies (e.g., PO link) and simulate pending payment.
        pr.sudo().write({"state": "submit"})
        with self.assertRaises(UserError):
            project.action_set_lifecycle_state("warranty")

    def test_payment_requires_settlement_approved(self):
        project = self._create_project("P0 Project Settle State", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="draft")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Draft Settle",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "draft",
            }
        )
        with self.assertRaises(UserError):
            pr.action_submit()

    def test_payment_overpay_blocked(self):
        project = self._create_project("P0 Project Overpay", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Overpay",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 200.0,
                "state": "draft",
            }
        )
        with self.assertRaises(UserError):
            pr.action_submit()

    def test_payment_write_approved_requires_tier(self):
        project = self._create_project("P0 Project Tier", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Tier",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "draft",
            }
        )
        with self.assertRaises(UserError):
            pr.write({"state": "approved"})

    def test_settlement_cancel_blocked_when_payments_exist(self):
        project = self._create_project("P0 Project Cancel", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Linked",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "approve",
            }
        )
        with self.assertRaises(UserError):
            settlement.action_cancel()
