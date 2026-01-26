# -*- coding: utf-8 -*-
import base64

from odoo import fields
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

    def _create_finance_user(self, login="p0_finance_user_state_closure"):
        finance_group = self.env.ref("smart_construction_core.group_sc_cap_finance_user")
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "P0 Finance User",
                "login": login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [finance_group.id])],
                "email": f"{login}@test.local",
            }
        )

    def _create_purchase_order(self, partner):
        product = self.env["product.product"].create(
            {
                "name": "P0 PO Product",
                "type": "service",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )
        po = self.env["purchase.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": product.name,
                            "product_id": product.id,
                            "product_qty": 1.0,
                            "product_uom": self.uom_unit.id,
                            "price_unit": 1.0,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        po.write({"state": "purchase"})
        return po

    def _enable_funding(self, project, cap=1000.0):
        project.write({"funding_enabled": True})
        self.env["project.funding.baseline"].create(
            {"project_id": project.id, "total_amount": cap, "state": "active"}
        )

    def _create_settlement_order(
        self, project, partner, contract, amount=100.0, state="approve", purchase_orders=None
    ):
        vals = {
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "settlement_type": "out",
            "line_ids": [(0, 0, {"name": "P0 Line", "qty": 1.0, "price_unit": amount})],
            "state": state,
        }
        purchase_orders = purchase_orders or self.env["purchase.order"]
        if purchase_orders:
            vals["purchase_order_ids"] = [(6, 0, purchase_orders.ids)]
        return self.env["sc.settlement.order"].create(vals)

    def _attach_dummy(self, record, name="test.pdf"):
        self.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": base64.b64encode(b"test").decode("ascii"),
                "res_model": record._name,
                "res_id": record.id,
                "mimetype": "application/pdf",
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
        purchase_order = self._create_purchase_order(partner)
        settlement = self._create_settlement_order(
            project,
            partner,
            contract,
            amount=100.0,
            state="approve",
            purchase_orders=purchase_order,
        )

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
        self._attach_dummy(pr)
        finance_user = self._create_finance_user()
        project.sudo().message_subscribe(partner_ids=[finance_user.partner_id.id])
        pr.with_user(finance_user).action_submit()
        self.assertEqual(pr.state, "submit")
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
