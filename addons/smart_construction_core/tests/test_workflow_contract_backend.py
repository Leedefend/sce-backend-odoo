# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.smart_construction_core import core_extension


@tagged("post_install", "-at_install", "workflow_contract_backend")
class TestWorkflowContractBackend(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "Workflow Contract Project"})
        self.partner = self.env["res.partner"].create({"name": "Workflow Contract Partner"})
        self.tax = self.env["account.tax"].create(
            {
                "name": "Workflow Contract VAT 9%",
                "amount": 9.0,
                "amount_type": "percent",
                "type_tax_use": "purchase",
                "price_include": False,
                "company_id": self.env.company.id,
            }
        )
        self.contract = self.env["construction.contract"].create(
            {
                "subject": "Workflow Contract",
                "type": "in",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "tax_id": self.tax.id,
            }
        )
        self.service = self.env["sc.workflow.contract.service"]

    def test_expense_claim_draft_contract_is_editable_and_submittable(self):
        claim = self.env["sc.expense.claim"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100.0,
                "summary": "workflow-contract-smoke",
            }
        )

        contract = self.service.describe_record(claim)

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertEqual(contract["approvalPhase"], "none")
        self.assertEqual(contract["editability"], "editable")
        self.assertIn("submit", {row["key"] for row in contract["availableActions"]})

    def test_profile_methods_resolve_to_existing_model_methods(self):
        profiles = self.service.PROFILE_BY_MODEL
        self.assertTrue(profiles)
        for model_name, profile in profiles.items():
            self.assertIn(model_name, self.env.registry)
            model = self.env[model_name]
            for action_key in set(profile.get("method_by_action", {})):
                method_name = profile.get("method_by_action", {}).get(action_key)
                if not method_name:
                    continue
                self.assertTrue(
                    hasattr(model, method_name),
                    "%s workflow action %s points to missing method %s" % (model_name, action_key, method_name),
                )

    def test_supported_model_contract_schema_is_frontend_stable(self):
        expense_contract_wrapper = self.env["construction.contract.expense"].search(
            [("contract_id", "=", self.contract.id)],
            limit=1,
        )
        if not expense_contract_wrapper:
            expense_contract_wrapper = self.env["construction.contract.expense"].create({"contract_id": self.contract.id})
        income_contract = self.env["construction.contract"].create(
            {
                "subject": "Workflow Income Contract",
                "type": "out",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "tax_id": self.tax.id,
            }
        )
        income_contract_wrapper = self.env["construction.contract.income"].search(
            [("contract_id", "=", income_contract.id)],
            limit=1,
        )
        if not income_contract_wrapper:
            income_contract_wrapper = self.env["construction.contract.income"].create({"contract_id": income_contract.id})
        records = [
            self.env["payment.request"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "amount": 10.0,
                }
            ),
            self.env["sc.settlement.order"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                }
            ),
            self.env["sc.expense.claim"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "amount": 10.0,
                    "summary": "workflow-contract-schema",
                }
            ),
            self.contract,
            expense_contract_wrapper,
            income_contract_wrapper,
            self.env["sc.payment.execution"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "contract_id": self.contract.id,
                    "paid_amount": 10.0,
                    "payment_account_no": "payer-schema",
                    "receipt_account_no": "payee-schema",
                }
            ),
            self.env["sc.receipt.income"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "contract_id": self.contract.id,
                    "amount": 10.0,
                    "receiving_account_no": "receiver-schema",
                }
            ),
            self.env["sc.invoice.registration"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "contract_id": self.contract.id,
                    "amount_total": 10.0,
                }
            ),
            self.env["sc.self.funding.registration"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "amount": 10.0,
                    "payment_account_name": "Company Account",
                    "partner_account_name": "Contractor Account",
                }
            ),
            self.env["sc.financing.loan"].create(
                {
                    "project_id": self.project.id,
                    "amount": 10.0,
                }
            ),
            self.env["sc.treasury.reconciliation"].create(
                {
                    "project_id": self.project.id,
                    "system_difference": 0.0,
                }
            ),
            self.env["sc.general.contract"].create(
                {
                    "project_id": self.project.id,
                    "partner_id": self.partner.id,
                    "contract_name": "Workflow General Contract",
                    "amount_total": 10.0,
                }
            ),
            self.env["sc.settlement.adjustment"].create(
                {
                    "project_id": self.project.id,
                    "contract_id": self.contract.id,
                    "partner_id": self.partner.id,
                    "item_name": "workflow adjustment",
                    "amount": 10.0,
                }
            ),
        ]

        self.assertTrue(
            {record._name for record in records}.issubset(set(self.service.PROFILE_BY_MODEL)),
        )
        for record in records:
            contract = self.service.describe_record(record)
            self._assert_workflow_contract_schema(contract, record)

    def test_deduction_bill_missing_lines_disables_submit(self):
        category = self.env["sc.business.category"].search([("code", "=", "finance.deduction.bill")], limit=1)
        self.assertTrue(category, "扣款单业务分类应已初始化。")
        claim = self.env["sc.expense.claim"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "business_category_id": category.id,
                "expense_type": "扣款单",
                "amount": 100.0,
                "summary": "workflow-deduction-gate",
            }
        )

        contract = self.service.describe_record(claim)
        submit = self._action(contract, "submit")

        self.assertIn("DEDUCTION_BILL_MISSING_LINES", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        self.assertEqual(submit["reason_code"], "DEDUCTION_BILL_MISSING_LINES")

    def test_settlement_submit_contract_separates_business_and_approval_phase(self):
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "state": "submit",
            }
        )

        contract = self.service.describe_record(settlement)

        self.assertEqual(contract["rawState"], "submit")
        self.assertEqual(contract["businessPhase"], "under_review")
        self.assertIn(contract["approvalPhase"], {"waiting", "pending", "approved", "none"})
        self.assertEqual(contract["editability"], "readonly")

    def test_settlement_missing_lines_disables_submit(self):
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
            }
        )

        contract = self.service.describe_record(settlement)
        submit = self._action(contract, "submit")

        self.assertIn("SETTLEMENT_MISSING_LINES", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        self.assertEqual(submit["reason_code"], "SETTLEMENT_MISSING_LINES")

    def test_settlement_invalid_line_gate_matches_backend_submit_guard(self):
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "line_ids": [
                    (0, 0, {"name": "valid-line", "contract_id": self.contract.id, "qty": 1.0, "price_unit": 100.0}),
                    (0, 0, {"name": "invalid-line", "contract_id": self.contract.id, "qty": 0.0, "price_unit": 1.0}),
                ],
            }
        )

        contract = self.service.describe_record(settlement)
        submit = self._action(contract, "submit")

        self.assertIn("SETTLEMENT_INVALID_LINE_QTY", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            settlement.action_submit()

    def test_payment_missing_basis_disables_submit(self):
        payment = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 10.0,
            }
        )

        contract = self.service.describe_record(payment)
        submit = self._action(contract, "submit")

        self.assertIn("PAYMENT_MISSING_BASIS", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        self.assertEqual(submit["reason_code"], "PAYMENT_MISSING_BASIS")

    def test_payment_done_contract_is_locked(self):
        payment = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 10.0,
                "state": "done",
            }
        )

        contract = self.service.describe_record(payment)

        self.assertEqual(contract["businessPhase"], "done")
        self.assertEqual(contract["editability"], "locked")
        self.assertEqual(contract["availableActions"], [])

    def test_construction_contract_approval_in_progress_disables_duplicate_submit(self):
        self.env.cr.execute(
            "UPDATE construction_contract SET validation_status=%s WHERE id=%s",
            ("waiting", self.contract.id),
        )
        self.contract.invalidate_recordset()

        contract = self.service.describe_record(self.contract)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn(contract["approvalPhase"], {"waiting", "pending"})
        self.assertIn("CONTRACT_APPROVAL_IN_PROGRESS", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])

    def test_construction_contract_missing_lines_disables_complete_and_backend_blocks_close(self):
        self.env.cr.execute(
            "UPDATE construction_contract SET state=%s, validation_status=%s WHERE id=%s",
            ("confirmed", "validated", self.contract.id),
        )
        self.contract.invalidate_recordset()

        contract = self.service.describe_record(self.contract)
        complete = self._action(contract, "complete")

        self.assertEqual(contract["rawState"], "confirmed")
        self.assertEqual(contract["businessPhase"], "approved")
        self.assertIn("CONTRACT_MISSING_LINES_FOR_CLOSE", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(complete["enabled"])
        with self.assertRaises(UserError):
            self.contract.action_close()

    def test_construction_contract_cancel_does_not_depend_on_user_email(self):
        user = self.env["res.users"].create(
            {
                "name": "Workflow Contract User Without Email",
                "login": "workflow_contract_no_email",
                "groups_id": [
                    (6, 0, [
                        self.env.ref("base.group_user").id,
                        self.env.ref("smart_construction_core.group_sc_cap_contract_user").id,
                        self.env.ref("smart_construction_core.group_sc_cap_finance_read").id,
                    ])
                ],
            }
        )
        self.assertFalse(user.email)

        self.contract.with_user(user).action_cancel()

        self.assertEqual(self.contract.state, "cancel")

    def test_payment_execution_missing_request_disables_submit_and_backend_blocks_confirm(self):
        execution = self.env["sc.payment.execution"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "paid_amount": 100.0,
                "payment_account_no": "payer-001",
                "receipt_account_no": "payee-001",
            }
        )

        contract = self.service.describe_record(execution)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("PAYMENT_EXECUTION_MISSING_REQUEST", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            execution.action_confirm()

    def test_receipt_income_missing_request_disables_submit_and_backend_blocks_confirm(self):
        receipt = self.env["sc.receipt.income"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "amount": 100.0,
                "receiving_account_no": "receive-001",
            }
        )

        contract = self.service.describe_record(receipt)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("RECEIPT_INCOME_MISSING_REQUEST", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            receipt.action_confirm()

    def test_invoice_registration_missing_invoice_no_disables_submit_and_backend_blocks_confirm(self):
        invoice = self.env["sc.invoice.registration"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "amount_total": 100.0,
            }
        )

        contract = self.service.describe_record(invoice)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("INVOICE_REGISTRATION_MISSING_INVOICE_NO", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            invoice.action_confirm()

    def test_self_funding_missing_attachment_disables_submit_and_backend_blocks_confirm(self):
        funding = self.env["sc.self.funding.registration"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100.0,
                "payment_account_name": "Company Account",
                "partner_account_name": "Contractor Account",
            }
        )

        contract = self.service.describe_record(funding)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("SELF_FUNDING_ATTACHMENT_REQUIRED", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            funding.action_confirm()

    def test_financing_loan_missing_partner_disables_submit_and_backend_blocks_confirm(self):
        loan = self.env["sc.financing.loan"].create(
            {
                "project_id": self.project.id,
                "amount": 100.0,
            }
        )

        contract = self.service.describe_record(loan)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("FINANCING_LOAN_MISSING_PARTNER", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            loan.action_confirm()

    def test_treasury_reconciliation_missing_ledger_disables_submit_and_backend_blocks_confirm(self):
        reconciliation = self.env["sc.treasury.reconciliation"].create(
            {
                "project_id": self.project.id,
                "system_difference": 0.0,
            }
        )

        contract = self.service.describe_record(reconciliation)
        submit = self._action(contract, "submit")

        self.assertEqual(contract["rawState"], "draft")
        self.assertEqual(contract["businessPhase"], "draft")
        self.assertIn("TREASURY_RECONCILIATION_MISSING_LEDGER", {row["reasonCode"] for row in contract["evidenceGate"]})
        self.assertFalse(submit["enabled"])
        with self.assertRaises(UserError):
            reconciliation.action_confirm()

    def test_v2_extension_hook_injects_workflow_contract_for_existing_form(self):
        claim = self.env["sc.expense.claim"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 50.0,
                "summary": "workflow-hook-smoke",
            }
        )
        source_contract = {
            "model": "sc.expense.claim",
            "view_type": "form",
            "record_id": claim.id,
        }
        base_contract = {
            "statusContract": {"globalStatus": {"pageAuth": "read"}},
            "runtimeContract": {},
        }

        projected = core_extension.smart_core_finalize_unified_page_contract_v2(
            self.env,
            base_contract,
            {"source_contract": source_contract, "view_type": "form"},
        )

        self.assertIsInstance(projected, dict)
        self.assertEqual(projected["workflowContract"]["model"], "sc.expense.claim")
        self.assertEqual(projected["workflowContract"]["businessPhase"], "draft")
        self.assertEqual(projected["runtimeContract"]["workflowContract"]["rawState"], "draft")
        self.assertEqual(projected["statusContract"]["globalStatus"]["workflowPhase"], "draft")

    def _action(self, contract, key):
        for row in contract["availableActions"]:
            if row["key"] == key:
                return row
        self.fail("missing workflow action: %s" % key)

    def _assert_workflow_contract_schema(self, contract, record):
        self.assertEqual(contract["source"]["kind"], "sc_backend_workflow_contract_v1")
        self.assertEqual(contract["model"], record._name)
        self.assertEqual(contract["record_id"], record.id)
        self.assertEqual(contract["stateField"], self.service.PROFILE_BY_MODEL[record._name]["state_field"])
        self.assertIsInstance(contract["rawState"], str)
        self.assertTrue(contract["businessPhase"])
        self.assertTrue(contract["approvalPhase"])
        self.assertIn(contract["editability"], {"editable", "readonly", "locked"})
        self.assertIsInstance(contract["statusbar"], dict)
        self.assertEqual(contract["statusbar"]["field"], "__workflow_phase")
        self.assertTrue(contract["statusbar"]["current"])
        self.assertTrue(contract["statusbar"]["readonly"])
        self.assertTrue(contract["statusbar"]["states"])
        self.assertIn(contract["statusbar"]["current"], {row["value"] for row in contract["statusbar"]["states"]})
        self.assertIsInstance(contract["evidenceGate"], list)
        self.assertIsInstance(contract["availableActions"], list)
        for gate in contract["evidenceGate"]:
            self.assertTrue(gate["reasonCode"])
            self.assertTrue(gate["message"])
            self.assertIsInstance(gate["actionKeys"], list)
            self.assertIn(gate["severity"], {"block", "warn", "info"})
        for action in contract["availableActions"]:
            self.assertTrue(action["key"])
            self.assertTrue(action["label"])
            self.assertIn(action["intent"], {"data.write", "server.object"})
            self.assertIn(action["kind"], {"save", "transition", "approval"})
            self.assertIn(action["enabled"], {True, False})
            self.assertEqual(action["target"]["model"], record._name)
            self.assertEqual(action["target"]["id"], record.id)
            self.assertEqual(action["target"]["method"], action["method"])
            if action["enabled"]:
                self.assertEqual(action["reason_code"], "")
                self.assertEqual(action["blocked_message"], "")
            else:
                self.assertTrue(action["reason_code"])
                self.assertTrue(action["blocked_message"])
