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

    def _create_income_contract(self, project, partner):
        tax = self._create_tax("P0 Output VAT 9%", tax_use="sale")
        return self.env["construction.contract"].create(
            {
                "subject": "P0 Income Contract",
                "type": "out",
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

    def _create_finance_manager(self, login="p0_finance_manager_state_closure"):
        finance_group = self.env.ref("smart_construction_core.group_sc_cap_finance_manager")
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "P0 Finance Manager",
                "login": login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [finance_group.id])],
                "email": f"{login}@test.local",
            }
        )

    def _create_material_manager(self, login="p0_material_manager_state_closure"):
        material_group = self.env.ref("smart_construction_core.group_sc_cap_material_manager")
        return self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "P0 Material Manager",
                "login": login,
                "company_id": self.company.id,
                "company_ids": [(6, 0, [self.company.id])],
                "groups_id": [(6, 0, [material_group.id])],
                "email": f"{login}@test.local",
            }
        )

    def _create_material_catalog(self, name="P0 Material Catalog"):
        return self.env["sc.material.catalog"].create(
            {
                "name": name,
                "code": name.replace(" ", "-").upper(),
                "company_id": self.company.id,
                "spec_model": "P0-SPEC",
                "uom_text": "件",
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
                "state": "purchase",
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

    def test_payment_settlement_not_approved_can_be_approved_with_advisory(self):
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
        finance_user = self._create_finance_user("p0_finance_user_settle_state")
        finance_manager = self._create_finance_manager("p0_finance_manager_settle_state")
        project.message_subscribe(partner_ids=finance_user.partner_id.ids)
        pr.with_user(finance_user).action_submit()
        pr.with_user(finance_manager).validate_tier()
        pr.invalidate_recordset()
        self.assertEqual(pr.state, "approved")

    def test_payment_overpay_can_be_approved_with_advisory(self):
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
        finance_user = self._create_finance_user("p0_finance_user_overpay")
        finance_manager = self._create_finance_manager("p0_finance_manager_overpay")
        project.message_subscribe(partner_ids=finance_user.partner_id.ids)
        pr.with_user(finance_user).action_submit()
        pr.with_user(finance_manager).validate_tier()
        pr.invalidate_recordset()
        self.assertEqual(pr.state, "approved")

    def test_payment_action_set_approved_closes_validated_approval(self):
        project = self._create_project("P0 Project Set Approved", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Set Approved",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "approve",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approve", "validated", pr.id),
        )
        pr.invalidate_recordset()

        pr.action_set_approved()
        pr.invalidate_recordset()
        self.assertEqual(pr.state, "approved")

    def test_payment_execution_paid_closes_payment_request(self):
        project = self._create_project("P0 Project Payment Execution", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")
        finance_manager = self._create_finance_manager("p0_finance_manager_payment_execution")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Payment Execution",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "approved",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", pr.id),
        )
        execution = self.env["sc.payment.execution"].sudo().create(
            {
                "payment_request_id": pr.id,
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "planned_amount": 10.0,
                "paid_amount": 10.0,
            }
        )
        self.env.cr.execute(
            "UPDATE sc_payment_execution SET state=%s, validation_status=%s WHERE id=%s",
            ("confirmed", "validated", execution.id),
        )
        pr.invalidate_recordset()
        execution.invalidate_recordset()

        execution.with_user(finance_manager).action_paid()
        pr.invalidate_recordset()
        execution.invalidate_recordset()
        ledger = self.env["payment.ledger"].search([("payment_request_id", "=", pr.id)])

        self.assertEqual(execution.state, "paid")
        self.assertEqual(pr.state, "done")
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger.amount, 10.0)

    def test_receipt_income_received_closes_receive_request(self):
        project = self._create_project("P0 Project Receipt Income", with_boq=True)
        partner = self._create_partner()
        contract = self._create_income_contract(project, partner)

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Receive Request",
                "type": "receive",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "amount": 10.0,
                "state": "approved",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", pr.id),
        )
        receipt = self.env["sc.receipt.income"].sudo().create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "payment_request_id": pr.id,
                "amount": 10.0,
            }
        )
        pr.invalidate_recordset()

        receipt.action_received()
        pr.invalidate_recordset()
        receipt.invalidate_recordset()
        treasury_ledger = self.env["sc.treasury.ledger"].search([("payment_request_id", "=", pr.id)])

        self.assertEqual(receipt.state, "received")
        self.assertEqual(pr.state, "done")
        self.assertEqual(len(treasury_ledger), 1)
        self.assertEqual(treasury_ledger.direction, "in")
        self.assertEqual(treasury_ledger.amount, 10.0)
        self.assertEqual(receipt.treasury_ledger_id, treasury_ledger)

    def test_payment_execution_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Project Payment Execution Block", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 PR Payment Execution Block",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "approved",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", pr.id),
        )
        execution = self.env["sc.payment.execution"].sudo().create(
            {
                "payment_request_id": pr.id,
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "planned_amount": 10.0,
                "paid_amount": 0.0,
            }
        )
        with self.assertRaises(UserError):
            execution.action_confirm()
        execution.write({"paid_amount": 10.0, "partner_id": False})
        with self.assertRaises(UserError):
            execution.action_paid()
        execution.write({"partner_id": partner.id})
        execution.action_confirm()
        with self.assertRaises(UserError):
            execution.action_confirm()
        execution.action_paid()
        with self.assertRaises(UserError):
            execution.action_cancel()

    def test_receipt_income_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Project Receipt Income Block", with_boq=True)
        partner = self._create_partner()
        contract = self._create_income_contract(project, partner)

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Receive Request Block",
                "type": "receive",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "amount": 10.0,
                "state": "approved",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", pr.id),
        )
        receipt = self.env["sc.receipt.income"].sudo().create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "payment_request_id": pr.id,
                "amount": 0.0,
            }
        )
        with self.assertRaises(UserError):
            receipt.action_confirm()
        receipt.write({"amount": 10.0, "partner_id": False})
        with self.assertRaises(UserError):
            receipt.action_received()
        receipt.write({"partner_id": partner.id})
        receipt.action_confirm()
        with self.assertRaises(UserError):
            receipt.action_confirm()
        receipt.action_received()
        with self.assertRaises(UserError):
            receipt.action_cancel()

    def test_expense_claim_done_closes_payment_request(self):
        project = self._create_project("P0 Project Expense Claim", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        self._enable_funding(project, cap=1000.0)
        settlement = self._create_settlement_order(project, partner, contract, amount=100.0, state="approve")

        pr = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Expense Payment Request",
                "type": "pay",
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_id": settlement.id,
                "amount": 10.0,
                "state": "approved",
            }
        )
        self.env.cr.execute(
            "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
            ("approved", "validated", pr.id),
        )
        claim = self.env["sc.expense.claim"].sudo().create(
            {
                "claim_type": "expense",
                "project_id": project.id,
                "partner_id": partner.id,
                "payment_request_id": pr.id,
                "amount": 10.0,
                "approved_amount": 10.0,
                "state": "approved",
            }
        )
        pr.invalidate_recordset()

        claim.action_done()
        pr.invalidate_recordset()
        claim.invalidate_recordset()
        ledger = self.env["payment.ledger"].search([("payment_request_id", "=", pr.id)])

        self.assertEqual(claim.state, "done")
        self.assertEqual(pr.state, "done")
        self.assertEqual(len(ledger), 1)
        self.assertEqual(ledger.amount, 10.0)

    def test_expense_claim_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Expense Claim State Block", with_boq=True)
        claim = self.env["sc.expense.claim"].sudo().create(
            {
                "claim_type": "expense",
                "project_id": project.id,
                "amount": 10.0,
                "approved_amount": 10.0,
            }
        )

        with self.assertRaises(UserError):
            claim.action_done()
        claim.action_submit()
        claim.invalidate_recordset()
        self.assertIn(claim.state, ("submit", "approved"))
        with self.assertRaises(UserError):
            claim.action_submit()
        if claim.state == "submit":
            claim.write({"state": "approved"})
        claim.action_done()
        claim.invalidate_recordset()
        self.assertEqual(claim.state, "done")
        with self.assertRaises(UserError):
            claim.action_done()
        with self.assertRaises(UserError):
            claim.action_cancel()

    def test_tax_deduction_action_deduct_defaults_and_closes(self):
        project = self._create_project("P0 Project Tax Deduction", with_boq=True)
        partner = self._create_partner()

        deduction = self.env["sc.tax.deduction.registration"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "invoice_no": "P0-TAX-001",
                "invoice_amount_untaxed": 100.0,
                "invoice_tax_amount": 9.0,
                "invoice_amount_total": 109.0,
            }
        )

        deduction.action_deduct()
        deduction.invalidate_recordset()

        self.assertEqual(deduction.state, "deducted")
        self.assertTrue(deduction.deduction_confirm_date)
        self.assertEqual(deduction.deduction_amount, 100.0)
        self.assertEqual(deduction.deduction_tax_amount, 9.0)

    def test_tax_deduction_action_deduct_blocks_over_deduction(self):
        project = self._create_project("P0 Project Tax Deduction Block", with_boq=True)
        partner = self._create_partner()

        deduction = self.env["sc.tax.deduction.registration"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "invoice_no": "P0-TAX-OVER",
                "invoice_amount_untaxed": 100.0,
                "invoice_tax_amount": 9.0,
                "invoice_amount_total": 109.0,
                "deduction_tax_amount": 10.0,
            }
        )

        with self.assertRaises(UserError):
            deduction.action_deduct()
        deduction.invalidate_recordset()
        self.assertEqual(deduction.state, "draft")

    def test_tax_deduction_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Tax Deduction State Block", with_boq=True)
        partner = self._create_partner()

        deduction = self.env["sc.tax.deduction.registration"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "invoice_no": "P0-TAX-STATE",
                "invoice_amount_untaxed": 100.0,
                "invoice_tax_amount": 9.0,
                "invoice_amount_total": 109.0,
            }
        )

        deduction.action_confirm()
        deduction.invalidate_recordset()
        self.assertEqual(deduction.state, "confirmed")
        with self.assertRaises(UserError):
            deduction.action_confirm()
        deduction.action_deduct()
        deduction.invalidate_recordset()
        self.assertEqual(deduction.state, "deducted")
        with self.assertRaises(UserError):
            deduction.action_deduct()
        with self.assertRaises(UserError):
            deduction.action_cancel()

    def test_treasury_reconciliation_requires_zero_difference_and_ledger(self):
        project = self._create_project("P0 Project Treasury Reconcile", with_boq=True)
        partner = self._create_partner()
        request = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Treasury Receive",
                "type": "receive",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 20.0,
                "state": "approved",
            }
        )
        ledger = (
            self.env["sc.treasury.ledger"]
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": project.id,
                    "partner_id": partner.id,
                    "payment_request_id": request.id,
                    "direction": "in",
                    "amount": 20.0,
                }
            )
        )
        reconciliation = self.env["sc.treasury.reconciliation"].create(
            {
                "project_id": project.id,
                "treasury_ledger_id": ledger.id,
                "account_balance": 20.0,
                "bank_balance": 20.0,
                "system_difference": 0.0,
            }
        )

        reconciliation.action_reconcile()
        reconciliation.invalidate_recordset()
        self.assertEqual(reconciliation.state, "reconciled")

    def test_treasury_reconciliation_blocks_unbalanced_difference(self):
        project = self._create_project("P0 Project Treasury Reconcile Block", with_boq=True)
        partner = self._create_partner()
        request = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Treasury Receive Block",
                "type": "receive",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 20.0,
                "state": "approved",
            }
        )
        ledger = (
            self.env["sc.treasury.ledger"]
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": project.id,
                    "partner_id": partner.id,
                    "payment_request_id": request.id,
                    "direction": "in",
                    "amount": 20.0,
                }
            )
        )
        reconciliation = self.env["sc.treasury.reconciliation"].create(
            {
                "project_id": project.id,
                "treasury_ledger_id": ledger.id,
                "account_balance": 20.0,
                "bank_balance": 19.0,
                "system_difference": 1.0,
            }
        )

        with self.assertRaises(UserError):
            reconciliation.action_reconcile()
        reconciliation.invalidate_recordset()
        self.assertEqual(reconciliation.state, "draft")

    def test_treasury_reconciliation_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Treasury Reconcile State Block", with_boq=True)
        partner = self._create_partner()
        request = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Treasury Receive State Block",
                "type": "receive",
                "project_id": project.id,
                "partner_id": partner.id,
                "amount": 20.0,
                "state": "approved",
            }
        )
        ledger = (
            self.env["sc.treasury.ledger"]
            .with_context(allow_ledger_auto=True)
            .create(
                {
                    "project_id": project.id,
                    "partner_id": partner.id,
                    "payment_request_id": request.id,
                    "direction": "in",
                    "amount": 20.0,
                }
            )
        )
        reconciliation = self.env["sc.treasury.reconciliation"].create(
            {
                "project_id": project.id,
                "treasury_ledger_id": ledger.id,
                "account_balance": 20.0,
                "bank_balance": 20.0,
                "system_difference": 0.0,
            }
        )

        reconciliation.action_confirm()
        reconciliation.invalidate_recordset()
        self.assertEqual(reconciliation.state, "confirmed")
        with self.assertRaises(UserError):
            reconciliation.action_confirm()
        reconciliation.action_reconcile()
        reconciliation.invalidate_recordset()
        self.assertEqual(reconciliation.state, "reconciled")
        with self.assertRaises(UserError):
            reconciliation.action_reconcile()
        with self.assertRaises(UserError):
            reconciliation.action_cancel()

    def test_financing_loan_done_requires_business_anchor(self):
        project = self._create_project("P0 Project Financing Loan", with_boq=True)
        partner = self._create_partner()
        loan = self.env["sc.financing.loan"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "loan_type": "loan_registration",
                "direction": "financing_in",
                "amount": 100.0,
            }
        )

        loan.action_done()
        loan.invalidate_recordset()
        self.assertEqual(loan.state, "done")

    def test_financing_loan_done_blocks_missing_anchor_or_amount(self):
        project = self._create_project("P0 Project Financing Loan Block", with_boq=True)
        loan = self.env["sc.financing.loan"].create(
            {
                "project_id": project.id,
                "loan_type": "borrowing_request",
                "direction": "borrowed_fund",
                "amount": 0.0,
            }
        )

        with self.assertRaises(UserError):
            loan.action_done()
        loan.invalidate_recordset()
        self.assertEqual(loan.state, "draft")

    def test_financing_loan_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Financing Loan State Block", with_boq=True)
        partner = self._create_partner()
        loan = self.env["sc.financing.loan"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "loan_type": "borrowing_request",
                "direction": "borrowed_fund",
                "amount": 100.0,
            }
        )

        loan.action_confirm()
        loan.invalidate_recordset()
        self.assertEqual(loan.state, "confirmed")
        with self.assertRaises(UserError):
            loan.action_confirm()
        loan.action_done()
        loan.invalidate_recordset()
        self.assertEqual(loan.state, "done")
        with self.assertRaises(UserError):
            loan.action_done()
        with self.assertRaises(UserError):
            loan.action_cancel()

    def test_construction_diary_done_requires_business_content(self):
        project = self._create_project("P0 Project Construction Diary", with_boq=True)
        diary = self.env["sc.construction.diary"].create(
            {
                "project_id": project.id,
                "title": "P0 Daily Site Log",
                "diary_type": "日报表",
                "manpower_count": 8,
                "description": "Site work completed as planned.",
            }
        )

        diary.action_done()
        diary.invalidate_recordset()
        self.assertEqual(diary.state, "done")

    def test_construction_diary_confirm_blocks_empty_content(self):
        project = self._create_project("P0 Project Construction Diary Block", with_boq=True)
        diary = self.env["sc.construction.diary"].create(
            {
                "project_id": project.id,
                "title": "P0 Empty Site Log",
                "diary_type": "日报表",
                "manpower_count": -1,
            }
        )

        with self.assertRaises(UserError):
            diary.action_confirm()
        diary.invalidate_recordset()
        self.assertEqual(diary.state, "draft")

    def test_construction_diary_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Construction Diary State Block", with_boq=True)
        diary = self.env["sc.construction.diary"].create(
            {
                "project_id": project.id,
                "title": "P0 Daily Site Log State Block",
                "diary_type": "日报表",
                "manpower_count": 8,
                "description": "Site work completed as planned.",
            }
        )

        diary.action_confirm()
        diary.invalidate_recordset()
        self.assertEqual(diary.state, "confirmed")
        with self.assertRaises(UserError):
            diary.action_confirm()
        diary.action_done()
        diary.invalidate_recordset()
        self.assertEqual(diary.state, "done")
        with self.assertRaises(UserError):
            diary.action_done()
        with self.assertRaises(UserError):
            diary.action_cancel()

    def test_fund_account_operation_confirm_done_requires_active_accounts(self):
        project = self._create_project("P0 Project Fund Account Operation", with_boq=True)
        source = self.env["sc.fund.account"].create(
            {"name": "P0 Source Account", "account_no": "FA-SRC", "project_id": project.id}
        )
        target = self.env["sc.fund.account"].create(
            {"name": "P0 Target Account", "account_no": "FA-TGT", "project_id": project.id}
        )
        operation = self.env["sc.fund.account.operation"].create(
            {
                "operation_type": "transfer_between",
                "source_account_id": source.id,
                "target_account_id": target.id,
                "project_id": project.id,
                "amount": 30.0,
                "operation_reason": "P0 transfer",
            }
        )

        operation.action_confirm()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, "confirmed")
        operation.action_done()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, "done")

    def test_fund_account_operation_blocks_inactive_or_unconfirmed_done(self):
        project = self._create_project("P0 Project Fund Account Operation Block", with_boq=True)
        source = self.env["sc.fund.account"].create(
            {"name": "P0 Inactive Source Account", "account_no": "FA-ISRC", "project_id": project.id}
        )
        target = self.env["sc.fund.account"].create(
            {"name": "P0 Active Target Account", "account_no": "FA-ATGT", "project_id": project.id}
        )
        operation = self.env["sc.fund.account.operation"].create(
            {
                "operation_type": "transfer_between",
                "source_account_id": source.id,
                "target_account_id": target.id,
                "project_id": project.id,
                "amount": 30.0,
                "operation_reason": "P0 blocked transfer",
            }
        )

        with self.assertRaises(UserError):
            operation.action_done()
        source.state = "inactive"
        with self.assertRaises(UserError):
            operation.action_confirm()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, "draft")

    def test_fund_account_operation_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Fund Account Operation State Block", with_boq=True)
        source = self.env["sc.fund.account"].create(
            {"name": "P0 Source Account State", "account_no": "FA-SSRC", "project_id": project.id}
        )
        target = self.env["sc.fund.account"].create(
            {"name": "P0 Target Account State", "account_no": "FA-STGT", "project_id": project.id}
        )
        operation = self.env["sc.fund.account.operation"].create(
            {
                "operation_type": "transfer_between",
                "source_account_id": source.id,
                "target_account_id": target.id,
                "project_id": project.id,
                "amount": 30.0,
                "operation_reason": "P0 state blocked transfer",
            }
        )

        with self.assertRaises(UserError):
            operation.action_reset_draft()
        operation.action_confirm()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, "confirmed")
        with self.assertRaises(UserError):
            operation.action_confirm()
        operation.action_done()
        operation.invalidate_recordset()
        self.assertEqual(operation.state, "done")
        with self.assertRaises(UserError):
            operation.action_cancel()
        with self.assertRaises(UserError):
            operation.action_reset_draft()

    def test_contract_event_submit_approve_done_requires_business_anchor(self):
        project = self._create_project("P0 Project Contract Event", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        event = self.env["sc.contract.event"].create(
            {
                "name": "P0 Contract Event",
                "event_type": "site_instruction",
                "project_id": project.id,
                "contract_id": contract.id,
                "partner_id": partner.id,
                "event_date": fields.Date.today(),
            }
        )

        event.action_submit()
        event.invalidate_recordset()
        self.assertEqual(event.state, "submitted")
        event.action_approve()
        event.invalidate_recordset()
        self.assertEqual(event.state, "approved")
        event.action_done()
        event.invalidate_recordset()
        self.assertEqual(event.state, "done")

    def test_contract_event_blocks_wrong_project_or_state_jump(self):
        project = self._create_project("P0 Project Contract Event Block", with_boq=True)
        other_project = self._create_project("P0 Project Contract Event Other", with_boq=True)
        partner = self._create_partner()
        other_contract = self._create_contract(other_project, partner)
        event = self.env["sc.contract.event"].create(
            {
                "name": "P0 Contract Event Block",
                "event_type": "claim",
                "project_id": project.id,
                "contract_id": other_contract.id,
                "partner_id": partner.id,
                "event_date": fields.Date.today(),
            }
        )

        with self.assertRaises(UserError):
            event.action_submit()
        with self.assertRaises(UserError):
            event.action_done()
        event.invalidate_recordset()
        self.assertEqual(event.state, "draft")

    def test_contract_event_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Contract Event State Block", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        event = self.env["sc.contract.event"].create(
            {
                "name": "P0 Contract Event State Block",
                "event_type": "site_instruction",
                "project_id": project.id,
                "contract_id": contract.id,
                "partner_id": partner.id,
                "event_date": fields.Date.today(),
            }
        )

        event.action_submit()
        event.invalidate_recordset()
        self.assertEqual(event.state, "submitted")
        cancel_event = event.copy({"name": "P0 Contract Event Cancel"})
        cancel_event.action_cancel()
        cancel_event.invalidate_recordset()
        self.assertEqual(cancel_event.state, "cancel")
        with self.assertRaises(UserError):
            cancel_event.action_cancel()
        event.action_approve()
        event.invalidate_recordset()
        self.assertEqual(event.state, "approved")
        with self.assertRaises(UserError):
            event.action_cancel()
        event.action_done()
        event.invalidate_recordset()
        self.assertEqual(event.state, "done")
        with self.assertRaises(UserError):
            event.action_cancel()

    def test_general_contract_confirm_signed_business_flow(self):
        project = self._create_project("P0 General Contract", with_boq=True)
        partner = self._create_partner("P0 General Contract Partner")
        contract = self.env["sc.general.contract"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_name": "P0 材料采购合同",
                "contract_type": "材料采购",
                "amount_total": 100.0,
            }
        )

        contract.action_confirm()
        contract.invalidate_recordset()
        self.assertEqual(contract.state, "draft")
        self.assertTrue(contract.review_ids)
        self.env.cr.execute(
            "UPDATE sc_general_contract SET validation_status=%s WHERE id=%s",
            ("validated", contract.id),
        )
        contract.invalidate_recordset()
        contract.action_on_tier_approved()
        contract.invalidate_recordset()
        self.assertEqual(contract.state, "confirmed")
        contract.action_signed()
        contract.invalidate_recordset()
        self.assertEqual(contract.state, "signed")

    def test_general_contract_blocks_invalid_anchor_or_terminal_cancel(self):
        project = self._create_project("P0 General Contract Block", with_boq=True)
        partner = self._create_partner("P0 General Contract Block Partner")
        contract = self.env["sc.general.contract"].create(
            {
                "project_id": project.id,
                "contract_name": "P0 无合同方合同",
                "contract_type": "材料采购",
                "amount_total": 100.0,
            }
        )

        with self.assertRaises(UserError):
            contract.action_confirm()
        contract.write({"partner_id": partner.id, "amount_total": 0.0})
        with self.assertRaises(UserError):
            contract.action_confirm()
        contract.write({"amount_total": 100.0, "contract_direction": "unknown"})
        with self.assertRaises(UserError):
            contract.action_confirm()
        contract.write({"contract_direction": "income"})
        contract.action_confirm()
        with self.assertRaises(UserError):
            contract.action_confirm()
        self.env.cr.execute(
            "UPDATE sc_general_contract SET validation_status=%s WHERE id=%s",
            ("validated", contract.id),
        )
        contract.invalidate_recordset()
        contract.action_on_tier_approved()
        contract.invalidate_recordset()
        self.assertEqual(contract.state, "confirmed")
        contract.action_signed()
        contract.invalidate_recordset()
        self.assertEqual(contract.state, "signed")
        with self.assertRaises(UserError):
            contract.action_cancel()

    def test_settlement_order_submit_approve_done_business_flow(self):
        project = self._create_project("P0 Settlement Order Flow", with_boq=True)
        partner = self._create_partner("P0 Settlement Order Partner")
        contract = self._create_contract(project, partner)
        purchase_order = self._create_purchase_order(partner)
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_type": "out",
                "purchase_order_ids": [(6, 0, purchase_order.ids)],
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "P0 Settlement Order Line",
                            "contract_id": contract.id,
                            "qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submit")
        self.assertTrue(settlement.review_ids)
        self.env.cr.execute(
            "UPDATE sc_settlement_order SET validation_status=%s WHERE id=%s",
            ("validated", settlement.id),
        )
        settlement.invalidate_recordset()
        settlement.action_on_tier_approved()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "approve")
        settlement.action_done()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "done")

    def test_settlement_order_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Settlement Order Block", with_boq=True)
        partner = self._create_partner("P0 Settlement Order Block Partner")
        contract = self._create_contract(project, partner)
        purchase_order = self._create_purchase_order(partner)
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "settlement_type": "out",
                "purchase_order_ids": [(6, 0, purchase_order.ids)],
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "P0 Settlement Order Block Line",
                            "contract_id": contract.id,
                            "qty": 0.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            settlement.action_submit()
        settlement.line_ids.write({"qty": 1.0, "price_unit": -1.0})
        with self.assertRaises(UserError):
            settlement.action_submit()
        settlement.line_ids.write({"price_unit": 100.0})
        with self.assertRaises(UserError):
            settlement.action_done()
        settlement.action_submit()
        with self.assertRaises(UserError):
            settlement.action_submit()
        with self.assertRaises(UserError):
            settlement.action_on_tier_approved()
        self.env.cr.execute(
            "UPDATE sc_settlement_order SET validation_status=%s WHERE id=%s",
            ("validated", settlement.id),
        )
        settlement.invalidate_recordset()
        settlement.action_on_tier_approved()
        settlement.action_done()
        with self.assertRaises(UserError):
            settlement.action_cancel()

    def test_project_settlement_confirm_done_requires_business_anchor(self):
        project = self._create_project("P0 Project Settlement Closure", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        settlement = self.env["project.settlement"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "amount": 100.0,
                "date_settle": fields.Date.today(),
            }
        )

        settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")
        settlement.action_done()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "done")

    def test_project_settlement_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Project Settlement Closure Block", with_boq=True)
        other_project = self._create_project("P0 Project Settlement Closure Other", with_boq=True)
        partner = self._create_partner()
        other_contract = self._create_contract(other_project, partner)
        settlement = self.env["project.settlement"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": other_contract.id,
                "amount": 0.0,
                "date_settle": fields.Date.today(),
            }
        )

        with self.assertRaises(UserError):
            settlement.action_done()
        with self.assertRaises(UserError):
            settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "draft")

    def test_invoice_registration_confirm_register_requires_business_anchor(self):
        project = self._create_project("P0 Project Invoice Registration", with_boq=True)
        partner = self._create_partner()
        contract = self._create_contract(project, partner)
        invoice = self.env["sc.invoice.registration"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract.id,
                "direction": "input",
                "source_kind": "invoice_registration",
                "invoice_no": "P0-INV-001",
                "invoice_date": fields.Date.today(),
                "amount_total": 109.0,
                "tax_amount": 9.0,
            }
        )

        invoice.action_confirm()
        invoice.invalidate_recordset()
        self.assertEqual(invoice.state, "confirmed")
        invoice.action_register()
        invoice.invalidate_recordset()
        self.assertEqual(invoice.state, "registered")
        with self.assertRaises(UserError):
            invoice.action_register()
        with self.assertRaises(UserError):
            invoice.action_cancel()

    def test_invoice_registration_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Project Invoice Registration Block", with_boq=True)
        other_project = self._create_project("P0 Project Invoice Registration Other", with_boq=True)
        partner = self._create_partner()
        other_contract = self._create_contract(other_project, partner)
        invoice = self.env["sc.invoice.registration"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": other_contract.id,
                "direction": "input",
                "source_kind": "invoice_registration",
                "invoice_date": fields.Date.today(),
                "amount_total": 0.0,
            }
        )

        with self.assertRaises(UserError):
            invoice.action_register()
        with self.assertRaises(UserError):
            invoice.action_confirm()
        invoice.invalidate_recordset()
        self.assertEqual(invoice.state, "draft")

        invoice.write(
            {
                "contract_id": False,
                "invoice_no": "P0-INV-BLOCK-001",
                "amount_total": 109.0,
                "tax_amount": 9.0,
            }
        )
        invoice.action_cancel()
        invoice.invalidate_recordset()
        self.assertEqual(invoice.state, "cancel")
        with self.assertRaises(UserError):
            invoice.action_confirm()
        with self.assertRaises(UserError):
            invoice.action_cancel()

    def test_material_rental_order_and_settlement_close_business_flow(self):
        project = self._create_project("P0 Project Material Rental", with_boq=True)
        supplier = self._create_partner("P0 Rental Supplier")
        contract = self._create_contract(project, supplier)
        plan = self.env["sc.material.rental.plan"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe",
                            "planned_qty": 10.0,
                            "planned_days": 5.0,
                            "daily_price": 2.0,
                        },
                    )
                ],
            }
        )
        plan.action_submit()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "submitted")
        plan.action_approve()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")
        order = self.env["sc.material.rental.order"].create(
            {
                "project_id": project.id,
                "plan_id": plan.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe",
                            "qty": 10.0,
                            "rental_days": 5.0,
                            "daily_price": 2.0,
                        },
                    )
                ],
            }
        )

        order.action_activate()
        order.invalidate_recordset()
        self.assertEqual(order.state, "active")
        order.action_return()
        order.invalidate_recordset()
        self.assertEqual(order.state, "returned")

        payment_request = self.env["payment.request"].sudo().create(
            {
                "name": "P0 Rental Payment",
                "type": "pay",
                "project_id": project.id,
                "partner_id": supplier.id,
                "contract_id": contract.id,
                "amount": 108.0,
            }
        )
        settlement = self.env["sc.material.rental.settlement"].create(
            {
                "project_id": project.id,
                "rental_order_id": order.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "payment_request_id": payment_request.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe",
                            "qty": 10.0,
                            "rental_days": 5.0,
                            "daily_price": 2.0,
                            "damage_amount": 8.0,
                        },
                    )
                ],
            }
        )

        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submitted")
        settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")
        settlement.action_paid()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "paid")

    def test_material_rental_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Project Material Rental Block", with_boq=True)
        supplier = self._create_partner("P0 Rental Supplier Block")
        contract = self._create_contract(project, supplier)
        plan = self.env["sc.material.rental.plan"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "state": "draft",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe Block",
                            "planned_qty": 10.0,
                            "planned_days": 5.0,
                            "daily_price": 2.0,
                        },
                    )
                ],
            }
        )
        order = self.env["sc.material.rental.order"].create(
            {
                "project_id": project.id,
                "plan_id": plan.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe Block",
                            "qty": 0.0,
                            "rental_days": 5.0,
                            "daily_price": 2.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            order.action_settle()
        with self.assertRaises(UserError):
            order.action_activate()
        order.invalidate_recordset()
        self.assertEqual(order.state, "draft")

        plan.line_ids.write({"planned_qty": 0.0})
        with self.assertRaises(UserError):
            plan.action_submit()
        plan.line_ids.write({"planned_qty": 10.0})
        plan.action_submit()
        with self.assertRaises(UserError):
            plan.action_submit()
        plan.action_cancel()
        with self.assertRaises(UserError):
            plan.action_approve()
        plan.action_reset_draft()
        with self.assertRaises(UserError):
            plan.action_reset_draft()

        settlement = self.env["sc.material.rental.settlement"].create(
            {
                "project_id": project.id,
                "rental_order_id": order.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "P0 Steel Pipe Block",
                            "qty": 1.0,
                            "rental_days": 1.0,
                            "daily_price": -1.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            settlement.action_paid()
        with self.assertRaises(UserError):
            settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "draft")

    def test_labor_usage_and_settlement_submit_confirm_business_flow(self):
        project = self._create_project("P0 Project Labor Flow", with_boq=True)
        contractor = self._create_partner("P0 Labor Contractor")
        usage = self.env["sc.labor.usage"].create(
            {
                "project_id": project.id,
                "contractor_id": contractor.id,
                "labor_team": "P0 Team",
                "work_content": "P0 masonry",
                "worker_qty": 3.0,
                "work_hours": 8.0,
            }
        )

        usage.action_submit()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "submitted")
        usage.action_confirm()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "confirmed")

        settlement = self.env["sc.labor.settlement"].create(
            {
                "project_id": project.id,
                "contractor_id": contractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "labor_team": "P0 Team",
                            "work_content": "P0 masonry",
                            "qty": 3.0,
                            "unit_name": "工日",
                            "unit_price": 100.0,
                            "tax_rate": 3.0,
                        },
                    )
                ],
            }
        )

        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submitted")
        settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")

    def test_labor_usage_and_settlement_block_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Labor Flow Block", with_boq=True)
        contractor = self._create_partner("P0 Labor Contractor Block")
        usage = self.env["sc.labor.usage"].create(
            {
                "project_id": project.id,
                "contractor_id": contractor.id,
                "labor_team": "P0 Team Block",
                "work_content": "P0 carpentry",
                "worker_qty": 2.0,
                "work_hours": 8.0,
            }
        )

        with self.assertRaises(UserError):
            usage.action_confirm()
        usage.action_submit()
        usage.action_confirm()
        with self.assertRaises(UserError):
            usage.action_cancel()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "confirmed")

        settlement = self.env["sc.labor.settlement"].create(
            {
                "project_id": project.id,
                "contractor_id": contractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "labor_team": "P0 Team Block",
                            "work_content": "P0 carpentry",
                            "qty": 2.0,
                            "unit_name": "工日",
                            "unit_price": 100.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            settlement.action_confirm()
        settlement.action_submit()
        settlement.action_confirm()
        with self.assertRaises(UserError):
            settlement.action_cancel()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")

    def test_equipment_usage_and_settlement_submit_confirm_business_flow(self):
        project = self._create_project("P0 Project Equipment Flow", with_boq=True)
        supplier = self._create_partner("P0 Equipment Supplier")
        usage = self.env["sc.equipment.usage"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "equipment_name": "P0 Tower Crane",
                "usage_location": "P0 Zone A",
                "operator_name": "P0 Operator",
                "usage_qty": 1.0,
                "usage_hours": 8.0,
            }
        )

        usage.action_submit()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "submitted")
        usage.action_confirm()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "confirmed")

        settlement = self.env["sc.equipment.settlement"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "usage_id": usage.id,
                            "equipment_name": "P0 Tower Crane",
                            "qty": 8.0,
                            "unit_price": 100.0,
                            "tax_rate": 3.0,
                        },
                    )
                ],
            }
        )

        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submitted")
        settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")

    def test_equipment_usage_and_settlement_block_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Project Equipment Flow Block", with_boq=True)
        supplier = self._create_partner("P0 Equipment Supplier Block")
        usage = self.env["sc.equipment.usage"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "equipment_name": "P0 Excavator",
                "usage_location": "P0 Zone B",
                "operator_name": "P0 Operator Block",
                "usage_qty": 1.0,
                "usage_hours": 8.0,
            }
        )

        with self.assertRaises(UserError):
            usage.action_confirm()
        usage.action_submit()
        usage.action_confirm()
        with self.assertRaises(UserError):
            usage.action_cancel()
        usage.invalidate_recordset()
        self.assertEqual(usage.state, "confirmed")

        settlement = self.env["sc.equipment.settlement"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "usage_id": usage.id,
                            "equipment_name": "P0 Excavator",
                            "qty": 8.0,
                            "unit_price": 100.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            settlement.action_confirm()
        settlement.action_submit()
        settlement.action_confirm()
        with self.assertRaises(UserError):
            settlement.action_cancel()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")

    def test_equipment_plan_and_request_submit_approve_business_flow(self):
        project = self._create_project("P0 Project Equipment Plan Request", with_boq=True)
        supplier = self._create_partner("P0 Equipment Plan Supplier")
        plan = self.env["sc.equipment.plan"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "usage_location": "P0 Zone C",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_name": "P0 Concrete Pump",
                            "planned_qty": 1.0,
                            "planned_hours": 8.0,
                            "usage_location": "P0 Zone C",
                        },
                    )
                ],
            }
        )

        plan.action_submit()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "submitted")
        plan.action_approve()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")

        request = self.env["sc.equipment.request"].create(
            {
                "project_id": project.id,
                "plan_id": plan.id,
                "supplier_id": supplier.id,
                "usage_location": "P0 Zone C",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_name": "P0 Concrete Pump",
                            "requested_qty": 1.0,
                            "planned_hours": 8.0,
                            "usage_location": "P0 Zone C",
                        },
                    )
                ],
            }
        )

        request.action_submit()
        request.invalidate_recordset()
        self.assertEqual(request.state, "submitted")
        request.action_approve()
        request.invalidate_recordset()
        self.assertEqual(request.state, "approved")

    def test_equipment_plan_and_request_block_state_jump_or_invalid_anchor(self):
        project = self._create_project("P0 Project Equipment Plan Request Block", with_boq=True)
        supplier = self._create_partner("P0 Equipment Plan Supplier Block")
        plan = self.env["sc.equipment.plan"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_name": "P0 Loader",
                            "planned_qty": 1.0,
                            "planned_hours": 8.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            plan.action_approve()
        plan.action_submit()
        plan.action_approve()
        with self.assertRaises(UserError):
            plan.action_cancel()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")

        draft_plan = self.env["sc.equipment.plan"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_name": "P0 Loader Draft",
                            "planned_qty": 1.0,
                            "planned_hours": 8.0,
                        },
                    )
                ],
            }
        )
        request = self.env["sc.equipment.request"].create(
            {
                "project_id": project.id,
                "plan_id": draft_plan.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "equipment_name": "P0 Loader Draft",
                            "requested_qty": 1.0,
                            "planned_hours": 8.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            request.action_approve()
        with self.assertRaises(UserError):
            request.action_submit()
        request.invalidate_recordset()
        self.assertEqual(request.state, "draft")

    def test_subcontract_plan_request_register_settlement_business_flow(self):
        project = self._create_project("P0 Project Subcontract Flow", with_boq=True)
        subcontractor = self._create_partner("P0 Subcontractor")
        contract = self._create_contract(project, subcontractor)
        plan = self.env["sc.subcontract.plan"].create(
            {
                "project_id": project.id,
                "contract_id": contract.id,
                "subcontract_scope": "P0 concrete structure",
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 concrete structure",
                            "planned_qty": 1.0,
                            "unit_name": "项",
                            "estimated_amount": 1000.0,
                        },
                    )
                ],
            }
        )

        plan.action_submit()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "submitted")
        plan.action_approve()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")

        request = self.env["sc.subcontract.request"].create(
            {
                "project_id": project.id,
                "plan_id": plan.id,
                "contract_id": contract.id,
                "subcontract_scope": "P0 concrete structure",
                "suggested_subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 concrete structure",
                            "required_qty": 1.0,
                            "unit_name": "项",
                            "estimated_amount": 1000.0,
                        },
                    )
                ],
            }
        )
        request.action_submit()
        request.invalidate_recordset()
        self.assertEqual(request.state, "submitted")
        request.action_approve()
        request.invalidate_recordset()
        self.assertEqual(request.state, "approved")

        register = self.env["sc.subcontract.register"].create(
            {
                "project_id": project.id,
                "request_id": request.id,
                "contract_id": contract.id,
                "subcontract_scope": "P0 concrete structure",
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 concrete structure",
                            "contract_qty": 1.0,
                            "unit_name": "项",
                            "registered_amount": 1000.0,
                        },
                    )
                ],
            }
        )
        register.action_register()
        register.invalidate_recordset()
        self.assertEqual(register.state, "active")

        settlement = self.env["sc.subcontract.settlement"].create(
            {
                "project_id": project.id,
                "register_id": register.id,
                "contract_id": contract.id,
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 concrete structure",
                            "qty": 1.0,
                            "unit_name": "项",
                            "unit_price": 1000.0,
                            "tax_rate": 3.0,
                        },
                    )
                ],
            }
        )
        settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "submitted")
        settlement.action_confirm()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "confirmed")

    def test_subcontract_flow_blocks_state_jump_or_invalid_anchor(self):
        project = self._create_project("P0 Project Subcontract Flow Block", with_boq=True)
        subcontractor = self._create_partner("P0 Subcontractor Block")
        contract = self._create_contract(project, subcontractor)
        plan = self.env["sc.subcontract.plan"].create(
            {
                "project_id": project.id,
                "contract_id": contract.id,
                "subcontract_scope": "P0 masonry",
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 masonry",
                            "planned_qty": 1.0,
                            "estimated_amount": 1000.0,
                        },
                    )
                ],
            }
        )

        with self.assertRaises(UserError):
            plan.action_approve()
        plan.action_submit()
        plan.action_approve()
        with self.assertRaises(UserError):
            plan.action_cancel()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")

        draft_plan = self.env["sc.subcontract.plan"].create(
            {
                "project_id": project.id,
                "subcontract_scope": "P0 masonry draft",
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 masonry draft",
                            "planned_qty": 1.0,
                            "estimated_amount": 1000.0,
                        },
                    )
                ],
            }
        )
        request = self.env["sc.subcontract.request"].create(
            {
                "project_id": project.id,
                "plan_id": draft_plan.id,
                "subcontract_scope": "P0 masonry draft",
                "suggested_subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 masonry draft",
                            "required_qty": 1.0,
                            "estimated_amount": 1000.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            request.action_approve()
        with self.assertRaises(UserError):
            request.action_submit()
        request.invalidate_recordset()
        self.assertEqual(request.state, "draft")

        register = self.env["sc.subcontract.register"].create(
            {
                "project_id": project.id,
                "request_id": request.id,
                "subcontract_scope": "P0 masonry draft",
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 masonry draft",
                            "contract_qty": 1.0,
                            "registered_amount": 1000.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            register.action_close()
        with self.assertRaises(UserError):
            register.action_register()
        register.invalidate_recordset()
        self.assertEqual(register.state, "draft")

        settlement = self.env["sc.subcontract.settlement"].create(
            {
                "project_id": project.id,
                "register_id": register.id,
                "subcontractor_id": subcontractor.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "work_scope": "P0 masonry draft",
                            "qty": 1.0,
                            "unit_price": 1000.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(UserError):
            settlement.action_confirm()
        with self.assertRaises(UserError):
            settlement.action_submit()
        settlement.invalidate_recordset()
        self.assertEqual(settlement.state, "draft")

    def test_labor_equipment_subcontract_price_lifecycle(self):
        project = self._create_project("P0 Project Price Lifecycle", with_boq=True)
        partner = self._create_partner("P0 Price Partner")
        price_specs = [
            (
                "sc.labor.price",
                {
                    "project_id": project.id,
                    "contractor_id": partner.id,
                    "work_content": "P0 masonry",
                    "unit_price": 100.0,
                    "tax_rate": 3.0,
                },
            ),
            (
                "sc.equipment.price",
                {
                    "project_id": project.id,
                    "supplier_id": partner.id,
                    "equipment_name": "P0 excavator",
                    "unit_price": 120.0,
                    "tax_rate": 3.0,
                },
            ),
            (
                "sc.subcontract.price",
                {
                    "project_id": project.id,
                    "subcontractor_id": partner.id,
                    "work_scope": "P0 concrete",
                    "unit_price": 1000.0,
                    "tax_rate": 3.0,
                },
            ),
        ]

        for model_name, vals in price_specs:
            price = self.env[model_name].create(vals)
            price.action_activate()
            price.invalidate_recordset()
            self.assertEqual(price.state, "active")
            price.action_deactivate()
            price.invalidate_recordset()
            self.assertEqual(price.state, "inactive")
            price.action_reset_draft()
            price.invalidate_recordset()
            self.assertEqual(price.state, "draft")

    def test_labor_equipment_subcontract_price_blocks_invalid_state_or_value(self):
        project = self._create_project("P0 Project Price Lifecycle Block", with_boq=True)
        partner = self._create_partner("P0 Price Partner Block")
        price_specs = [
            (
                "sc.labor.price",
                {
                    "project_id": project.id,
                    "contractor_id": partner.id,
                    "work_content": "P0 labor price block",
                    "unit_price": 100.0,
                },
                {"unit_price": -1.0},
            ),
            (
                "sc.equipment.price",
                {
                    "project_id": project.id,
                    "supplier_id": partner.id,
                    "equipment_name": "P0 equipment price block",
                    "unit_price": 120.0,
                },
                {"tax_rate": -1.0},
            ),
            (
                "sc.subcontract.price",
                {
                    "project_id": project.id,
                    "subcontractor_id": partner.id,
                    "work_scope": "P0 subcontract price block",
                    "unit_price": 1000.0,
                },
                {"unit_price": -1.0},
            ),
        ]

        for model_name, vals, invalid_vals in price_specs:
            price = self.env[model_name].create(vals)
            with self.assertRaises(UserError):
                price.action_deactivate()
            with self.assertRaises(UserError):
                price.action_reset_draft()
            with self.assertRaises(ValidationError):
                self.env[model_name].create({**vals, **invalid_vals})

    def test_plan_confirm_start_done_business_flow(self):
        project = self._create_project("P0 Project Plan Flow", with_boq=True)
        plan = self.env["sc.plan"].create(
            {
                "name": "P0 Plan Flow",
                "project_id": project.id,
                "planned_start": fields.Date.today(),
                "planned_finish": fields.Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "P0 Plan Node",
                            "planned_start": fields.Date.today(),
                            "planned_finish": fields.Date.today(),
                            "progress_rate": 100.0,
                            "state": "done",
                        },
                    )
                ],
            }
        )

        plan.action_confirm()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "confirmed")
        plan.action_start()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "in_progress")
        self.assertTrue(plan.actual_start)
        plan.action_done()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "done")
        self.assertTrue(plan.actual_finish)

    def test_plan_blocks_state_jump_or_missing_anchor(self):
        project = self._create_project("P0 Project Plan Flow Block", with_boq=True)
        empty_plan = self.env["sc.plan"].create({"name": "P0 Empty Plan", "project_id": project.id})

        with self.assertRaises(UserError):
            empty_plan.action_start()
        with self.assertRaises(UserError):
            empty_plan.action_confirm()
        empty_plan.invalidate_recordset()
        self.assertEqual(empty_plan.state, "draft")

        plan = self.env["sc.plan"].create(
            {
                "name": "P0 Blocked Plan",
                "project_id": project.id,
                "planned_start": fields.Date.today(),
                "planned_finish": fields.Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "P0 Unfinished Node",
                            "planned_start": fields.Date.today(),
                            "planned_finish": fields.Date.today(),
                            "progress_rate": 50.0,
                            "state": "in_progress",
                        },
                    )
                ],
            }
        )
        plan.action_confirm()
        plan.action_start()
        with self.assertRaises(UserError):
            plan.action_done()
        with self.assertRaises(UserError):
            plan.action_reset_draft()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "in_progress")

    def test_quality_issue_rectification_recheck_business_flow(self):
        project = self._create_project("P0 Project Quality Issue Flow", with_boq=True)
        issue = self.env["sc.quality.issue"].create(
            {
                "name": "P0 Quality Issue Flow",
                "project_id": project.id,
                "location": "A1",
                "description": "Concrete surface defect",
            }
        )

        issue.action_submit()
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "submitted")
        self.env["sc.quality.rectification"].create(
            {
                "issue_id": issue.id,
                "result": "Polished and repaired",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rectifying")
        issue.action_request_recheck()
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rechecking")
        self.env["sc.quality.recheck"].create(
            {
                "issue_id": issue.id,
                "result": "failed",
                "comment": "Need second repair",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rectifying")
        issue.action_request_recheck()
        self.env["sc.quality.recheck"].create(
            {
                "issue_id": issue.id,
                "result": "passed",
                "comment": "Accepted",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "closed")
        self.assertTrue(issue.closed_date)

    def test_quality_issue_blocks_invalid_state_or_missing_anchor(self):
        project = self._create_project("P0 Project Quality Issue Block", with_boq=True)
        empty_issue = self.env["sc.quality.issue"].create(
            {
                "name": "P0 Empty Quality Issue",
                "project_id": project.id,
            }
        )

        with self.assertRaises(UserError):
            empty_issue.action_submit()
        with self.assertRaises(UserError):
            empty_issue.action_start_rectification()
        with self.assertRaises(UserError):
            self.env["sc.quality.rectification"].create(
                {
                    "issue_id": empty_issue.id,
                    "result": "Invalid rectification",
                }
            )
        with self.assertRaises(UserError):
            self.env["sc.quality.recheck"].create(
                {
                    "issue_id": empty_issue.id,
                    "result": "passed",
                }
            )
        empty_issue.invalidate_recordset()
        self.assertEqual(empty_issue.state, "draft")

    def test_safety_issue_rectification_recheck_business_flow(self):
        project = self._create_project("P0 Project Safety Issue Flow", with_boq=True)
        issue = self.env["sc.safety.issue"].create(
            {
                "name": "P0 Safety Issue Flow",
                "project_id": project.id,
                "location": "B2",
                "description": "Missing edge protection",
            }
        )

        issue.action_submit()
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "submitted")
        self.env["sc.safety.rectification"].create(
            {
                "issue_id": issue.id,
                "result": "Installed guardrail",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rectifying")
        issue.action_request_recheck()
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rechecking")
        self.env["sc.safety.recheck"].create(
            {
                "issue_id": issue.id,
                "result": "failed",
                "comment": "Guardrail needs reinforcement",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "rectifying")
        issue.action_request_recheck()
        self.env["sc.safety.recheck"].create(
            {
                "issue_id": issue.id,
                "result": "passed",
                "comment": "Accepted",
            }
        )
        issue.invalidate_recordset()
        self.assertEqual(issue.state, "closed")
        self.assertTrue(issue.closed_date)

    def test_safety_issue_blocks_invalid_state_or_missing_anchor(self):
        project = self._create_project("P0 Project Safety Issue Block", with_boq=True)
        empty_issue = self.env["sc.safety.issue"].create(
            {
                "name": "P0 Empty Safety Issue",
                "project_id": project.id,
            }
        )

        with self.assertRaises(UserError):
            empty_issue.action_submit()
        with self.assertRaises(UserError):
            empty_issue.action_start_rectification()
        with self.assertRaises(UserError):
            self.env["sc.safety.rectification"].create(
                {
                    "issue_id": empty_issue.id,
                    "result": "Invalid rectification",
                }
            )
        with self.assertRaises(UserError):
            self.env["sc.safety.recheck"].create(
                {
                    "issue_id": empty_issue.id,
                    "result": "passed",
                }
            )
        empty_issue.invalidate_recordset()
        self.assertEqual(empty_issue.state, "draft")

    def test_safety_plan_and_disclosure_business_flow(self):
        project = self._create_project("P0 Project Safety Plan Flow", with_boq=True)
        plan = self.env["sc.safety.plan"].create(
            {
                "name": "P0 Safety Plan Flow",
                "project_id": project.id,
                "description": "Safety plan content",
            }
        )

        plan.action_submit()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "submitted")
        plan.action_approve()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")

        disclosure = self.env["sc.safety.disclosure"].create(
            {
                "name": "P0 Safety Disclosure Flow",
                "project_id": project.id,
                "safety_plan_id": plan.id,
                "participant_note": "Foreman and crew",
                "content": "Edge protection and daily inspection",
            }
        )
        disclosure.action_submit()
        disclosure.invalidate_recordset()
        self.assertEqual(disclosure.state, "submitted")
        disclosure.action_approve()
        disclosure.invalidate_recordset()
        self.assertEqual(disclosure.state, "approved")

    def test_safety_plan_and_disclosure_block_invalid_anchor_or_state(self):
        project = self._create_project("P0 Project Safety Plan Block", with_boq=True)
        empty_plan = self.env["sc.safety.plan"].create(
            {
                "name": "P0 Empty Safety Plan",
                "project_id": project.id,
            }
        )

        with self.assertRaises(UserError):
            empty_plan.action_submit()
        with self.assertRaises(UserError):
            empty_plan.action_approve()
        empty_plan.invalidate_recordset()
        self.assertEqual(empty_plan.state, "draft")

        unapproved_plan = self.env["sc.safety.plan"].create(
            {
                "name": "P0 Unapproved Safety Plan",
                "project_id": project.id,
                "description": "Safety plan content",
            }
        )
        disclosure = self.env["sc.safety.disclosure"].create(
            {
                "name": "P0 Blocked Safety Disclosure",
                "project_id": project.id,
                "safety_plan_id": unapproved_plan.id,
                "participant_note": "Crew",
                "content": "Safety briefing",
            }
        )
        with self.assertRaises(UserError):
            disclosure.action_submit()
        disclosure.write({"safety_plan_id": False, "content": False})
        with self.assertRaises(UserError):
            disclosure.action_submit()
        disclosure.invalidate_recordset()
        self.assertEqual(disclosure.state, "draft")

    def test_project_risk_action_claim_escalate_close_business_flow(self):
        project = self._create_project("P0 Project Risk Action Flow", with_boq=True)
        action = self.env["project.risk.action"].create(
            {
                "name": "P0 Risk Action Flow",
                "project_id": project.id,
                "risk_level": "high",
            }
        )

        action.action_claim()
        action.invalidate_recordset()
        self.assertEqual(action.state, "claimed")
        self.assertEqual(action.owner_id, self.env.user)
        action.action_escalate(note="Escalate to project manager")
        action.invalidate_recordset()
        self.assertEqual(action.state, "escalated")
        self.assertIn("Escalate to project manager", action.note)
        action.action_close(note="Handled")
        action.invalidate_recordset()
        self.assertEqual(action.state, "closed")
        self.assertIn("Handled", action.note)

    def test_project_risk_action_blocks_invalid_state_or_missing_owner(self):
        project = self._create_project("P0 Project Risk Action Block", with_boq=True)
        action = self.env["project.risk.action"].create(
            {
                "name": "P0 Risk Action Block",
                "project_id": project.id,
                "risk_level": "critical",
            }
        )

        with self.assertRaises(UserError):
            action.action_close()
        action.action_escalate(note="Urgent")
        action.invalidate_recordset()
        self.assertEqual(action.state, "escalated")
        with self.assertRaises(UserError):
            action.action_claim()
        with self.assertRaises(UserError):
            action.action_close()
        action.write({"owner_id": self.env.user.id})
        action.action_close(note="Closed")
        with self.assertRaises(UserError):
            action.action_escalate(note="Invalid after close")
        action.invalidate_recordset()
        self.assertEqual(action.state, "closed")

    def test_hazard_source_and_safety_patrol_business_flow(self):
        project = self._create_project("P0 Project Hazard Patrol Flow", with_boq=True)
        hazard = self.env["sc.hazard.source"].create(
            {
                "name": "P0 Hazard Flow",
                "project_id": project.id,
                "location": "Tower crane area",
                "valid_from": fields.Date.today(),
                "valid_to": fields.Date.today(),
            }
        )

        hazard.action_report()
        hazard.invalidate_recordset()
        self.assertEqual(hazard.state, "reported")
        hazard.action_control()
        hazard.invalidate_recordset()
        self.assertEqual(hazard.state, "controlled")
        self.assertEqual(hazard.control_status, "controlled")
        hazard.action_close()
        hazard.invalidate_recordset()
        self.assertEqual(hazard.state, "closed")

        task = self.env["sc.safety.patrol.task"].create(
            {
                "name": "P0 Safety Patrol Flow",
                "project_id": project.id,
                "planned_date": fields.Date.today(),
                "score": 90.0,
                "pass_rate": 95.0,
            }
        )
        task.action_plan()
        task.invalidate_recordset()
        self.assertEqual(task.state, "planned")
        task.action_done()
        task.invalidate_recordset()
        self.assertEqual(task.state, "done")

    def test_hazard_source_and_safety_patrol_block_invalid_anchor_or_state(self):
        project = self._create_project("P0 Project Hazard Patrol Block", with_boq=True)
        hazard = self.env["sc.hazard.source"].create(
            {
                "name": "P0 Empty Hazard",
                "project_id": project.id,
                "valid_from": fields.Date.today(),
                "valid_to": fields.Date.today(),
            }
        )

        with self.assertRaises(UserError):
            hazard.action_report()
        hazard.write({"location": "Lift entrance", "valid_from": fields.Date.today(), "valid_to": fields.Date.today()})
        hazard.action_report()
        with self.assertRaises(UserError):
            hazard.action_report()
        with self.assertRaises(UserError):
            hazard.action_close()
        hazard.invalidate_recordset()
        self.assertEqual(hazard.state, "reported")

        task = self.env["sc.safety.patrol.task"].create(
            {
                "name": "P0 Empty Safety Patrol",
                "project_id": project.id,
            }
        )
        with self.assertRaises(UserError):
            task.action_plan()
        task.write({"planned_date": fields.Date.today(), "pass_rate": 120.0})
        task.action_plan()
        with self.assertRaises(UserError):
            task.action_done()
        task.invalidate_recordset()
        self.assertEqual(task.state, "planned")

    def test_settlement_adjustment_confirm_cancel_business_flow(self):
        project = self._create_project("P0 Project Settlement Adjustment Flow", with_boq=True)
        partner = self._create_partner("P0 Settlement Adjustment Partner")
        contract = self._create_contract(project, partner)
        purchase_order = self._create_purchase_order(partner)
        settlement = self._create_settlement_order(
            project,
            partner,
            contract,
            amount=100.0,
            state="approve",
            purchase_orders=purchase_order,
        )
        adjustment = self.env["sc.settlement.adjustment"].create(
            {
                "settlement_id": settlement.id,
                "adjustment_type": "deduction",
                "item_name": "P0 Deduction",
                "amount": 10.0,
            }
        )

        adjustment.action_confirm()
        adjustment.invalidate_recordset()
        settlement.invalidate_recordset()
        self.assertEqual(adjustment.state, "confirmed")
        self.assertEqual(adjustment.signed_amount, -10.0)
        self.assertEqual(settlement.adjustment_total, -10.0)
        self.assertEqual(settlement.amount_after_adjustment, 90.0)
        adjustment.action_cancel()
        adjustment.invalidate_recordset()
        self.assertEqual(adjustment.state, "cancel")

    def test_settlement_adjustment_blocks_invalid_anchor_or_state(self):
        project = self._create_project("P0 Project Settlement Adjustment Block", with_boq=True)
        partner = self._create_partner("P0 Settlement Adjustment Block Partner")
        contract = self._create_contract(project, partner)
        adjustment = self.env["sc.settlement.adjustment"].create(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "adjustment_type": "addition",
                "amount": 10.0,
            }
        )

        with self.assertRaises(UserError):
            adjustment.action_confirm()
        adjustment.write({"item_name": "P0 Addition"})
        with self.assertRaises(UserError):
            adjustment.action_confirm()
        adjustment.write({"contract_id": contract.id, "amount": 0.0})
        with self.assertRaises(UserError):
            adjustment.action_confirm()
        adjustment.write({"amount": 20.0})
        adjustment.action_cancel()
        with self.assertRaises(UserError):
            adjustment.action_confirm()
        adjustment.invalidate_recordset()
        self.assertEqual(adjustment.state, "cancel")

    def test_project_progress_entry_submit_business_flow(self):
        project = self._create_project("P0 Project Progress Entry Flow", with_boq=True)
        wbs = self.env["construction.work.breakdown"].create(
            {
                "name": "P0 Progress WBS",
                "code": "P0-WBS",
                "project_id": project.id,
                "level_type": "sub_section",
            }
        )
        entry = self.env["project.progress.entry"].create(
            {
                "project_id": project.id,
                "wbs_id": wbs.id,
                "qty_done": 5.0,
                "qty_cum": 5.0,
                "progress_rate": 50.0,
            }
        )

        entry.action_submit_progress()
        entry.invalidate_recordset()
        self.assertEqual(entry.state, "submitted")
        with self.assertRaises(UserError):
            entry.write({"qty_done": 6.0})

    def test_project_progress_entry_blocks_invalid_anchor_or_state(self):
        project = self._create_project("P0 Project Progress Entry Block", with_boq=True)
        wbs = self.env["construction.work.breakdown"].create(
            {
                "name": "P0 Progress Block WBS",
                "code": "P0-WBS-BLOCK",
                "project_id": project.id,
                "level_type": "sub_section",
            }
        )
        entry = self.env["project.progress.entry"].create(
            {
                "project_id": project.id,
                "wbs_id": wbs.id,
                "progress_rate": 10.0,
            }
        )

        with self.assertRaises(UserError):
            entry.action_submit_progress()
        entry.write({"qty_done": 1.0, "progress_rate": 120.0})
        with self.assertRaises(UserError):
            entry.action_submit_progress()
        entry.write({"progress_rate": 10.0})
        entry.action_submit_progress()
        with self.assertRaises(UserError):
            entry.action_submit_progress()
        entry.invalidate_recordset()
        self.assertEqual(entry.state, "submitted")

    def test_material_plan_submit_approve_done_business_flow(self):
        project = self._create_project("P0 Material Plan Flow", with_boq=True)
        manager = self._create_material_manager()
        catalog = self._create_material_catalog("P0 Material Plan Catalog")
        plan = self.env["project.material.plan"].create(
            {
                "project_id": project.id,
                "date_plan": fields.Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_catalog_id": catalog.id,
                            "quantity": 5.0,
                        },
                    )
                ],
            }
        )

        plan.with_user(manager).action_submit()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "submit")
        self.assertTrue(plan.review_ids)
        self.env.cr.execute(
            "UPDATE project_material_plan SET validation_status=%s WHERE id=%s",
            ("validated", plan.id),
        )
        plan.invalidate_recordset()
        plan.with_user(manager).action_on_tier_approved()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "approved")
        plan.with_user(manager).action_done()
        plan.invalidate_recordset()
        self.assertEqual(plan.state, "done")

    def test_material_plan_blocks_invalid_anchor_or_state_jump(self):
        project = self._create_project("P0 Material Plan Block", with_boq=True)
        manager = self._create_material_manager("p0_material_manager_state_closure_block")
        catalog = self._create_material_catalog("P0 Material Plan Block Catalog")
        plan = self.env["project.material.plan"].create(
            {
                "project_id": project.id,
                "date_plan": fields.Date.today(),
                "line_ids": [(0, 0, {"quantity": 5.0})],
            }
        )

        with self.assertRaises(UserError):
            plan.with_user(manager).action_submit()
        plan.line_ids.write({"material_catalog_id": catalog.id, "quantity": 0.0})
        with self.assertRaises(UserError):
            plan.with_user(manager).action_submit()
        plan.line_ids.write({"quantity": 5.0})
        with self.assertRaises(UserError):
            plan.with_user(manager).action_done()
        plan.with_user(manager).action_submit()
        with self.assertRaises(UserError):
            plan.with_user(manager).action_submit()
        with self.assertRaises(UserError):
            plan.with_user(manager).action_on_tier_approved()
        self.env.cr.execute(
            "UPDATE project_material_plan SET validation_status=%s WHERE id=%s",
            ("validated", plan.id),
        )
        plan.invalidate_recordset()
        plan.with_user(manager).action_on_tier_approved()
        plan.with_user(manager).action_done()
        with self.assertRaises(UserError):
            plan.with_user(manager).action_cancel()

    def test_material_purchase_stock_and_settlement_business_flow(self):
        project = self._create_project("P0 Material Flow", with_boq=True)
        supplier = self._create_partner("P0 Material Supplier")
        product = self.env["product.product"].create(
            {
                "name": "P0 Material Product",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )

        request = self.env["sc.material.purchase.request"].create(
            {
                "project_id": project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": self.uom_unit.id,
                            "qty": 10.0,
                            "estimated_unit_price": 5.0,
                        },
                    )
                ],
            }
        )
        request.action_submit()
        request.action_approve()
        self.assertEqual(request.state, "approved")

        acceptance = self.env["sc.material.acceptance"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "purchase_request_id": request.id,
            }
        )
        acceptance.action_submit()
        acceptance.action_accept()
        self.assertEqual(acceptance.state, "accepted")

        inbound = self.env["sc.material.inbound"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "acceptance_id": acceptance.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": self.uom_unit.id,
                            "qty": 10.0,
                            "unit_price": 5.0,
                        },
                    )
                ],
            }
        )
        inbound.action_submit()
        inbound.action_receive()
        self.assertEqual(inbound.state, "received")

        outbound = self.env["sc.material.outbound"].create(
            {
                "project_id": project.id,
                "receiver_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": self.uom_unit.id,
                            "qty": 3.0,
                        },
                    )
                ],
            }
        )
        outbound.action_submit()
        outbound.action_issue()
        self.assertEqual(outbound.state, "issued")

        rfq = self.env["sc.material.rfq"].create(
            {
                "project_id": project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "supplier_id": supplier.id,
                            "product_id": product.id,
                            "product_uom_id": self.uom_unit.id,
                            "qty": 10.0,
                            "unit_price": 5.0,
                            "selected": True,
                        },
                    )
                ],
            }
        )
        rfq.action_submit()
        rfq.action_select()
        self.assertEqual(rfq.state, "selected")

        settlement = self.env["sc.material.settlement"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_id": self.uom_unit.id,
                            "qty": 10.0,
                            "unit_price": 5.0,
                        },
                    )
                ],
            }
        )
        settlement.action_submit()
        settlement.action_confirm()
        self.assertEqual(settlement.state, "confirmed")

    def test_material_flow_blocks_invalid_state_jump_or_late_cancel(self):
        project = self._create_project("P0 Material Block", with_boq=True)
        supplier = self._create_partner("P0 Material Block Supplier")
        product = self.env["product.product"].create(
            {
                "name": "P0 Material Block Product",
                "type": "product",
                "uom_id": self.uom_unit.id,
                "uom_po_id": self.uom_unit.id,
            }
        )
        line_vals = {
            "product_id": product.id,
            "product_uom_id": self.uom_unit.id,
            "qty": 1.0,
        }

        request = self.env["sc.material.purchase.request"].create(
            {"project_id": project.id, "line_ids": [(0, 0, line_vals)]}
        )
        with self.assertRaises(ValidationError):
            request.action_approve()
        request.action_submit()
        request.action_approve()
        with self.assertRaises(ValidationError):
            request.action_cancel()

        acceptance = self.env["sc.material.acceptance"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [(0, 0, {"product_id": product.id, "received_qty": 1.0})],
            }
        )
        with self.assertRaises(ValidationError):
            acceptance.action_accept()
        acceptance.action_submit()
        acceptance.action_accept()
        with self.assertRaises(ValidationError):
            acceptance.action_cancel()

        inbound = self.env["sc.material.inbound"].create(
            {"project_id": project.id, "line_ids": [(0, 0, line_vals)]}
        )
        with self.assertRaises(ValidationError):
            inbound.action_receive()
        inbound.action_submit()
        inbound.action_receive()
        with self.assertRaises(ValidationError):
            inbound.action_cancel()

        outbound = self.env["sc.material.outbound"].create(
            {"project_id": project.id, "line_ids": [(0, 0, line_vals)]}
        )
        with self.assertRaises(ValidationError):
            outbound.action_issue()
        outbound.action_submit()
        outbound.action_issue()
        with self.assertRaises(ValidationError):
            outbound.action_cancel()

        rfq = self.env["sc.material.rfq"].create(
            {
                "project_id": project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "supplier_id": supplier.id,
                            "product_id": product.id,
                            "qty": 1.0,
                            "unit_price": 1.0,
                            "selected": True,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(ValidationError):
            rfq.action_select()
        rfq.action_submit()
        rfq.action_select()
        with self.assertRaises(ValidationError):
            rfq.action_cancel()

        settlement = self.env["sc.material.settlement"].create(
            {
                "project_id": project.id,
                "supplier_id": supplier.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "qty": 1.0,
                            "unit_price": 1.0,
                        },
                    )
                ],
            }
        )
        with self.assertRaises(ValidationError):
            settlement.action_confirm()
        settlement.action_submit()
        settlement.action_confirm()
        with self.assertRaises(ValidationError):
            settlement.action_cancel()

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
