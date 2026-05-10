# -*- coding: utf-8 -*-
import re

from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "user_feedback")
class TestUserFeedbackBusinessViews(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "User Feedback Project"})
        self.product = self.env["product.product"].create({"name": "User Feedback Material", "type": "product"})
        self.partner = self.env["res.partner"].create({"name": "User Feedback Partner"})
        if not self.env["stock.warehouse"].search([], limit=1):
            self.env["stock.warehouse"].create({"name": "Feedback Warehouse", "code": "UFB"})

    def test_material_inbound_can_be_created_with_business_amounts(self):
        inbound = self.env["sc.material.inbound"].create(
            {
                "project_id": self.project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "qty": 2,
                            "unit_price": 15,
                            "note": "feedback-save-smoke",
                        },
                    )
                ],
            }
        )

        self.assertTrue(inbound.warehouse_id, "入库单应自动带出默认入库仓库，避免填单保存失败。")
        self.assertTrue(inbound.dest_location_id, "入库单应自动带出默认入库库位，避免填单保存失败。")
        self.assertEqual(inbound.line_ids.amount, 30)
        self.assertEqual(inbound.amount_total, 30)
        self.assertEqual(inbound.material_name_summary, self.product.display_name)
        self.assertEqual(inbound.total_qty, 2)
        self.assertEqual(inbound.unit_price_summary, "15")
        self.assertEqual(inbound.line_note_summary, "feedback-save-smoke")

    def test_material_inbound_list_exposes_line_business_summaries(self):
        view = self.env.ref("smart_construction_core.view_sc_material_inbound_tree")
        arch = view.arch_db

        self.assertIn('name="material_name_summary"', arch)
        self.assertIn('name="material_spec_summary"', arch)
        self.assertIn('name="material_uom_summary"', arch)
        self.assertIn('name="total_qty" sum="入库数量合计"', arch)
        self.assertIn('name="unit_price_summary"', arch)
        self.assertIn('name="line_note_summary"', arch)
        self.assertIn('name="amount_total" sum="金额合计"', arch)

    def test_material_inbound_system_defaults_do_not_block_draft_creation(self):
        inbound = self.env["sc.material.inbound"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "note": "system-default-smoke",
                        },
                    )
                ],
            }
        )

        self.assertTrue(inbound.project_id)
        self.assertTrue(inbound.warehouse_id)
        self.assertTrue(inbound.dest_location_id)
        self.assertTrue(inbound.sc_has_system_default)
        self.assertIn("project_id", inbound.sc_system_default_fields)
        self.assertTrue(inbound.line_ids.product_id)
        self.assertEqual(inbound.line_ids.qty, 1)
        self.assertTrue(inbound.line_ids.sc_has_system_default)
        self.assertIn("product_id", inbound.line_ids.sc_system_default_fields)

    def test_material_system_defaults_warn_but_do_not_block_submit(self):
        inbound = self.env["sc.material.inbound"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "note": "system-default-submit-warning",
                        },
                    )
                ],
            }
        )

        inbound.action_submit()

        self.assertEqual(inbound.state, "submitted")
        warning_messages = inbound.message_ids.filtered(
            lambda message: "系统默认兜底值" in (message.body or "")
        )
        self.assertTrue(warning_messages)
        self.assertIn("不阻断业务推进", warning_messages[0].body)

    def test_material_required_child_defaults_are_strategy_based(self):
        rfq = self.env["sc.material.rfq"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "note": "rfq-default-smoke",
                        },
                    )
                ],
            }
        )
        settlement = self.env["sc.material.settlement"].create(
            {
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "note": "settlement-default-smoke",
                        },
                    )
                ],
            }
        )

        self.assertTrue(rfq.sc_has_system_default)
        self.assertTrue(rfq.line_ids.supplier_id)
        self.assertTrue(rfq.line_ids.product_id)
        self.assertEqual(rfq.line_ids.qty, 1)
        self.assertEqual(rfq.line_ids.unit_price, 0)
        self.assertTrue(rfq.line_ids.sc_has_system_default)
        self.assertTrue(settlement.project_id)
        self.assertTrue(settlement.supplier_id)
        self.assertTrue(settlement.line_ids.product_id)
        self.assertEqual(settlement.line_ids.qty, 1)
        self.assertEqual(settlement.line_ids.unit_price, 0)

    def test_supplier_business_fields_are_available(self):
        supplier = self.env["res.partner"].create(
            {
                "name": "Feedback Supplier",
                "supplier_rank": 1,
                "sc_supplier_type": "material",
                "sc_account_name": "Feedback Supplier",
                "sc_bank_name": "Feedback Bank",
                "sc_bank_account": "100200300",
                "vat": "91510000FEEDBACK",
                "sc_region": "四川",
                "legacy_partner_id": "SUP-OLD-001",
                "legacy_partner_source": "supplier_master",
                "legacy_partner_name": "旧库供应商",
                "legacy_deleted_flag": "0",
            }
        )
        action = self.env.ref("smart_construction_core.action_sc_supplier_partner")
        tree = self.env.ref("smart_construction_core.view_sc_supplier_partner_tree")
        form = self.env.ref("smart_construction_core.view_sc_supplier_partner_form")
        search = self.env.ref("smart_construction_core.view_sc_supplier_partner_search")

        self.assertEqual(supplier.sc_supplier_type, "material")
        self.assertEqual(supplier.sc_supplier_type_label, "材料供应商")
        labor_type = self.env.ref("smart_construction_core.sc_supplier_type_labor")
        equipment_type = self.env.ref("smart_construction_core.sc_supplier_type_equipment")
        supplier.write({"sc_supplier_type_ids": [(6, 0, [labor_type.id, equipment_type.id])]})
        self.assertEqual(supplier.sc_supplier_type, "labor")
        self.assertEqual(supplier.sc_supplier_type_label, "劳务供应商、设备供应商")
        self.assertEqual(supplier.sc_bank_account, "100200300")
        self.assertEqual(supplier._fields["legacy_partner_id"].string, "历史供应商编号")
        self.assertIn("'active_test': False", action.context)
        self.assertIn('name="sc_supplier_type_label"', tree.arch_db)
        self.assertIn('name="sc_supplier_type_ids"', form.arch_db)
        self.assertIn('name="legacy_partner_id"', tree.arch_db)
        self.assertIn('name="legacy_partner_source"', tree.arch_db)
        self.assertIn('name="legacy_partner_name"', form.arch_db)
        self.assertIn('name="legacy_deleted_flag"', search.arch_db)

    @tagged("post_install", "-at_install", "user_feedback", "partner_role_alignment")
    def test_partner_roles_align_from_contract_receipt_and_expenditure_facts(self):
        tax = self.env["account.tax"].search([("amount", "=", 0), ("amount_type", "=", "percent")], limit=1)
        if not tax:
            tax = self.env["account.tax"].create(
                {
                    "name": "Feedback 0%",
                    "amount": 0,
                    "amount_type": "percent",
                    "type_tax_use": "sale",
                }
            )
        contract_customer = self.env["res.partner"].create({"name": "Feedback Contract Customer"})
        receipt_customer = self.env["res.partner"].create({"name": "Feedback Receipt Customer"})
        supplier = self.env["res.partner"].create({"name": "Feedback Expenditure Supplier"})
        stale = self.env["res.partner"].create({"name": "Feedback Stale Supplier", "supplier_rank": 1})

        self.env["construction.contract"].create(
            {
                "subject": "Feedback Income Contract",
                "type": "out",
                "project_id": self.project.id,
                "partner_id": contract_customer.id,
                "tax_id": tax.id,
            }
        )
        self.env["sc.receipt.income"].create(
            {
                "name": "FB-RCPT-001",
                "project_id": self.project.id,
                "partner_id": receipt_customer.id,
                "amount": 123,
                "receiving_account_name": "Feedback Receipt Customer",
                "receiving_bank_name": "Feedback Bank",
                "receiving_account_no": "62220001",
            }
        )
        self.env["payment.request"].create(
            {
                "name": "FB-PAY-001",
                "type": "pay",
                "project_id": self.project.id,
                "partner_id": supplier.id,
                "amount": 456,
            }
        )

        summary = self.env["res.partner"].action_sc_align_partner_roles_from_business_facts(demote_no_fact=True)
        self.env.invalidate_all()
        contract_customer = self.env["res.partner"].browse(contract_customer.id)
        receipt_customer = self.env["res.partner"].browse(receipt_customer.id)
        supplier = self.env["res.partner"].browse(supplier.id)
        stale = self.env["res.partner"].browse(stale.id)

        self.assertEqual(summary["status"], "PASS")
        self.assertEqual(contract_customer.customer_rank, 1)
        self.assertEqual(contract_customer.supplier_rank, 0)
        self.assertEqual(receipt_customer.customer_rank, 1)
        self.assertEqual(receipt_customer.supplier_rank, 0)
        self.assertEqual(receipt_customer.sc_source_receipt_amount, 123)
        self.assertEqual(receipt_customer.sc_bank_name, "Feedback Bank")
        self.assertEqual(receipt_customer.sc_bank_account, "62220001")
        self.assertEqual(supplier.customer_rank, 0)
        self.assertEqual(supplier.supplier_rank, 1)
        self.assertEqual(supplier.sc_source_payment_amount, 456)
        self.assertEqual(stale.supplier_rank, 0)

    def test_material_rfq_exposes_contact_and_supplier_set(self):
        supplier = self.env["res.partner"].create(
            {"name": "Feedback RFQ Supplier", "supplier_rank": 1, "phone": "028-100000"}
        )
        supplier_b = self.env["res.partner"].create(
            {"name": "Feedback RFQ Supplier B", "supplier_rank": 1, "mobile": "13900000000"}
        )
        rfq = self.env["sc.material.rfq"].create(
            {
                "project_id": self.project.id,
                "contact_name": "张三",
                "contact_phone": "13800000000",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "supplier_id": supplier.id,
                            "product_id": self.product.id,
                            "qty": 2,
                            "unit_price": 11,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "supplier_id": supplier_b.id,
                            "product_id": self.product.id,
                            "qty": 2,
                            "unit_price": 12,
                            "quote_status": "quoted",
                        },
                    ),
                ],
            }
        )

        self.assertEqual(rfq.contact_name, "张三")
        self.assertEqual(rfq.supplier_ids, supplier | supplier_b)
        first_line = rfq.line_ids.filtered(lambda line: line.supplier_id == supplier)
        second_line = rfq.line_ids.filtered(lambda line: line.supplier_id == supplier_b)
        self.assertEqual(first_line.supplier_contact_phone, "028-100000")
        self.assertEqual(second_line.supplier_contact_phone, "13900000000")
        self.assertEqual(second_line.quote_status, "quoted")

    def test_material_request_acceptance_inbound_chain_carries_business_fields(self):
        request = self.env["sc.material.purchase.request"].create(
            {
                "project_id": self.project.id,
                "note": "request chain note",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "material_spec": "Spec-A",
                            "qty": 3,
                            "estimated_unit_price": 17,
                            "note": "line chain note",
                        },
                    )
                ],
            }
        )
        acceptance = self.env["sc.material.acceptance"].create(
            {
                "purchase_request_id": request.id,
            }
        )
        inbound = self.env["sc.material.inbound"].create(
            {
                "acceptance_id": acceptance.id,
            }
        )
        inbound.action_load_acceptance_lines()

        self.assertEqual(acceptance.project_id, self.project)
        self.assertEqual(acceptance.note, "request chain note")
        self.assertEqual(acceptance.line_ids.purchase_request_line_id, request.line_ids)
        self.assertEqual(acceptance.line_ids.product_id, self.product)
        self.assertEqual(acceptance.line_ids.material_spec, "Spec-A")
        self.assertEqual(acceptance.line_ids.planned_qty, 3)
        self.assertEqual(acceptance.line_ids.accepted_qty, 3)
        self.assertEqual(acceptance.line_ids.issue_note, "line chain note")
        self.assertEqual(inbound.project_id, self.project)
        self.assertEqual(inbound.line_ids.acceptance_line_id, acceptance.line_ids)
        self.assertEqual(inbound.line_ids.qty, 3)
        self.assertEqual(inbound.line_ids.unit_price, 17)
        self.assertEqual(inbound.line_ids.amount, 51)
        self.assertEqual(inbound.line_ids.note, "line chain note")

    def test_material_plan_generates_internal_rfq_with_plan_fields(self):
        self.env.user.groups_id |= self.env.ref("smart_construction_core.group_sc_cap_material_user")
        supplier = self.env["res.partner"].create({"name": "Plan RFQ Supplier", "supplier_rank": 1})
        plan = self.env["project.material.plan"].create(
            {
                "project_id": self.project.id,
                "state": "approved",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "spec": "Plan-Spec",
                            "quantity": 4,
                            "vendor_id": supplier.id,
                            "note": "plan line note",
                        },
                    )
                ],
            }
        )
        wizard = self.env["material.plan.to.rfq.wizard"].with_context(
            active_model="project.material.plan",
            active_ids=plan.ids,
        ).create(
            {
                "partner_id": supplier.id,
                "note": "plan rfq note",
            }
        )

        action = wizard.action_generate_rfq()
        rfq = self.env["sc.material.rfq"].browse(action["domain"][0][2])

        self.assertEqual(action["res_model"], "sc.material.rfq")
        self.assertEqual(rfq.project_id, self.project)
        self.assertEqual(rfq.source_material_plan_id, plan)
        self.assertEqual(rfq.note, "plan rfq note")
        self.assertEqual(rfq.line_ids.source_material_plan_line_id, plan.line_ids)
        self.assertEqual(rfq.line_ids.supplier_id, supplier)
        self.assertEqual(rfq.line_ids.product_id, self.product)
        self.assertEqual(rfq.line_ids.material_spec, "Plan-Spec")
        self.assertEqual(rfq.line_ids.qty, 4)
        self.assertEqual(rfq.line_ids.note, "plan line note")

    def test_material_plan_rfq_wizard_can_generate_multi_supplier_quotes(self):
        self.env.user.groups_id |= self.env.ref("smart_construction_core.group_sc_cap_material_user")
        supplier = self.env["res.partner"].create({"name": "Plan RFQ Multi Supplier A", "supplier_rank": 1})
        supplier_b = self.env["res.partner"].create({"name": "Plan RFQ Multi Supplier B", "supplier_rank": 1})
        plan = self.env["project.material.plan"].create(
            {
                "project_id": self.project.id,
                "state": "approved",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "spec": "Multi-Spec",
                            "quantity": 6,
                            "vendor_id": supplier.id,
                        },
                    )
                ],
            }
        )
        wizard = self.env["material.plan.to.rfq.wizard"].with_context(
            active_model="project.material.plan",
            active_ids=plan.ids,
        ).create(
            {
                "partner_id": supplier.id,
                "partner_ids": [(6, 0, [supplier_b.id])],
            }
        )

        action = wizard.action_generate_rfq()
        rfq = self.env["sc.material.rfq"].browse(action["domain"][0][2])

        self.assertEqual(rfq.supplier_ids, supplier | supplier_b)
        self.assertEqual(len(rfq.line_ids), 2)
        self.assertEqual(set(rfq.line_ids.mapped("supplier_id").ids), set((supplier | supplier_b).ids))
        self.assertEqual(set(rfq.line_ids.mapped("source_material_plan_line_id").ids), {plan.line_ids.id})
        self.assertEqual(set(rfq.line_ids.mapped("qty")), {6})

    def test_material_plan_list_exposes_line_business_summaries(self):
        plan = self.env["project.material.plan"].create(
            {
                "project_id": self.project.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "spec": "List-Spec",
                            "quantity": 7,
                            "bill_qty": 10,
                            "note": "list summary note",
                        },
                    )
                ],
            }
        )
        view = self.env.ref("smart_construction_core.view_project_material_plan_tree")
        arch = view.arch_db

        self.assertIn('name="material_name_summary"', arch)
        self.assertIn('name="material_spec_summary"', arch)
        self.assertIn('name="material_uom_summary"', arch)
        self.assertIn('name="line_note_summary"', arch)
        self.assertIn('name="line_attachment_count"', arch)
        self.assertEqual(plan.material_name_summary, self.product.display_name)
        self.assertEqual(plan.material_spec_summary, "List-Spec")
        self.assertTrue(plan.material_uom_summary)
        self.assertEqual(plan.total_plan_qty, 7)
        self.assertEqual(plan.total_bill_qty, 10)
        self.assertEqual(plan.total_unplanned_qty, 3)
        self.assertEqual(plan.line_note_summary, "list summary note")

    def test_material_rfq_purchase_acceptance_chain_carries_sources(self):
        supplier = self.env["res.partner"].create({"name": "RFQ Purchase Supplier", "supplier_rank": 1})
        plan = self.env["project.material.plan"].create(
            {
                "project_id": self.project.id,
                "state": "approved",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "spec": "PO-Spec",
                            "quantity": 5,
                            "vendor_id": supplier.id,
                        },
                    )
                ],
            }
        )
        rfq = self.env["sc.material.rfq"].create(
            {
                "project_id": self.project.id,
                "source_material_plan_id": plan.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "source_material_plan_line_id": plan.line_ids.id,
                            "supplier_id": supplier.id,
                            "product_id": self.product.id,
                            "material_spec": "PO-Spec",
                            "qty": 5,
                            "unit_price": 23,
                            "quote_status": "quoted",
                            "selected": True,
                            "note": "rfq selected line",
                        },
                    )
                ],
            }
        )

        action = rfq.action_create_purchase_order()
        purchase_order = self.env["purchase.order"].browse(action["res_id"])
        acceptance = self.env["sc.material.acceptance"].create({"purchase_order_id": purchase_order.id})
        acceptance.action_load_purchase_order_lines()

        self.assertEqual(purchase_order.source_material_rfq_id, rfq)
        self.assertEqual(purchase_order.project_id, self.project)
        self.assertEqual(purchase_order.plan_id, plan)
        self.assertEqual(purchase_order.order_line.source_material_rfq_line_id, rfq.line_ids)
        self.assertEqual(purchase_order.order_line.plan_line_id, plan.line_ids)
        self.assertEqual(purchase_order.order_line.product_qty, 5)
        self.assertEqual(purchase_order.order_line.price_unit, 23)
        self.assertEqual(acceptance.project_id, self.project)
        self.assertEqual(acceptance.supplier_id, supplier)
        self.assertEqual(acceptance.line_ids.purchase_order_line_id, purchase_order.order_line)
        self.assertEqual(acceptance.line_ids.product_id, self.product)
        self.assertEqual(acceptance.line_ids.material_spec, "PO-Spec")
        self.assertEqual(acceptance.line_ids.planned_qty, 5)
        self.assertEqual(acceptance.line_ids.accepted_qty, 5)

    def test_contract_execution_amounts_come_from_business_documents(self):
        contract = self.env["construction.contract"].create(
            {
                "subject": "Feedback Contract",
                "type": "out",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
            }
        )
        self.env["sc.invoice.registration"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "amount_total": 120,
            }
        )
        self.env["sc.receipt.income"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "amount": 80,
            }
        )
        self.env["sc.payment.execution"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": contract.id,
                "paid_amount": 50,
            }
        )

        self.assertEqual(contract.invoice_amount, 120)
        self.assertEqual(contract.received_amount, 80)
        self.assertEqual(contract.paid_amount, 50)

    def test_contract_list_exposes_legacy_contract_numbers(self):
        contract = self.env["construction.contract"].create(
            {
                "subject": "Feedback Legacy Contract No",
                "type": "out",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "legacy_contract_no": "HT-OLD-001",
                "legacy_document_no": "DJ-OLD-001",
                "legacy_external_contract_no": "WB-OLD-001",
            }
        )
        view = self.env.ref("smart_construction_core.view_construction_contract_tree")
        form = self.env.ref("smart_construction_core.view_construction_contract_form")

        self.assertEqual(contract.name[:3], "CON")
        self.assertEqual(contract.legacy_contract_no, "HT-OLD-001")
        self.assertEqual(contract._fields["name"].string, "单据编号")
        self.assertEqual(contract._fields["legacy_contract_no"].string, "合同编号")
        self.assertIn('name="legacy_contract_no"', view.arch_db)
        self.assertIn('name="legacy_external_contract_no"', view.arch_db)
        self.assertIn('name="legacy_document_no"', form.arch_db)
        self.assertIn('name="settlement_amount" sum="结算金额合计"', view.arch_db)
        self.assertIn('name="invoice_amount" sum="开票金额合计"', view.arch_db)
        self.assertIn('name="unpaid_amount" sum="未付款金额合计"', view.arch_db)

    def test_legacy_purchase_contract_is_not_business_approval_target(self):
        policy = self.env["sc.approval.policy"].get_active_policy("sc.legacy.purchase.contract.fact")
        self.assertFalse(policy)

        models = self.env["tier.definition"]._get_tier_validation_model_names()
        self.assertNotIn("sc.legacy.purchase.contract.fact", models)

    def test_general_contract_company_view_exposes_contact_columns(self):
        view = self.env.ref("smart_construction_core.view_sc_general_contract_tree")
        form = self.env.ref("smart_construction_core.view_sc_general_contract_form")
        arch = view.arch_db
        contract = self.env["sc.general.contract"].create(
            {
                "project_id": self.project.id,
                "contract_name": "Feedback General Contract",
                "amount_total": 100,
                "document_no": "SP-OLD-001",
                "contract_no": "HT-OLD-GEN-001",
                "submitted_time": "2026-05-03 10:30:00",
                "sign_status": "已签署",
                "signing_place": "成都",
                "expected_sign_date": "2026-05-06",
                "completion_date": "2026-06-01",
                "contact_name": "李四",
                "contact_phone": "13800001111",
            }
        )

        self.assertIn('tree string="一般合同（公司）"', arch)
        self.assertEqual(contract.submitted_time.strftime("%Y-%m-%d %H:%M:%S"), "2026-05-03 10:30:00")
        self.assertEqual(contract.sign_status, "已签署")
        self.assertEqual(contract._fields["document_no"].string, "审批编号")
        self.assertEqual(contract._fields["contract_no"].string, "合同编号")
        self.assertEqual(contract._fields["signing_place"].string, "合同签订地点")
        self.assertEqual(contract._fields["expected_sign_date"].string, "合同预计签订日期")
        self.assertEqual(contract._fields["completion_date"].string, "计划交货或完工日期")
        self.assertIn('name="contact_name"', arch)
        self.assertIn('name="contact_phone"', arch)
        self.assertIn('name="submitted_time"', arch)
        self.assertIn('name="sign_status"', arch)
        self.assertIn('name="signing_place"', form.arch_db)
        self.assertIn('name="expected_sign_date"', form.arch_db)
        self.assertIn('name="completion_date"', form.arch_db)

    def test_finance_projection_lists_expose_projected_business_fields(self):
        receipt_tree = self.env.ref("smart_construction_core.view_sc_receipt_income_tree").arch_db
        payment_tree = self.env.ref("smart_construction_core.view_sc_payment_execution_tree").arch_db
        invoice_tree = self.env.ref("smart_construction_core.view_sc_invoice_registration_tree").arch_db
        reconciliation_tree = self.env.ref("smart_construction_core.view_sc_treasury_reconciliation_tree").arch_db
        financing_tree = self.env.ref("smart_construction_core.view_sc_financing_loan_tree").arch_db

        for field_name in ("payment_method", "receiving_account", "bill_no", "invoice_ref"):
            self.assertIn('name="%s"' % field_name, receipt_tree)
        self.assertIn('name="deducted_invoice_amount" sum="已抵发票金额"', receipt_tree)
        self.assertIn('name="deducted_tax_amount" sum="已抵税额"', receipt_tree)
        self.assertIn('name="settlement_amount" sum="结算金额"', receipt_tree)

        for field_name in ("payment_family", "bank_account", "handler_name"):
            self.assertIn('name="%s"' % field_name, payment_tree)
        self.assertIn('name="invoice_amount" sum="发票金额"', payment_tree)

        for field_name in (
            "document_no",
            "document_date",
            "contract_id",
            "settlement_id",
            "invoice_code",
            "tax_rate",
            "invoice_content",
            "cost_category_name",
            "handler_name",
            "invoice_holder",
            "accounting_state",
            "voucher_no",
        ):
            self.assertIn('name="%s"' % field_name, invoice_tree)

        for field_name in ("source_kind", "bank_account_no"):
            self.assertIn('name="%s"' % field_name, reconciliation_tree)
        self.assertIn('name="account_balance" sum="账面余额"', reconciliation_tree)
        self.assertIn('name="bank_balance" sum="银行余额"', reconciliation_tree)

        for field_name in ("purpose", "rate_label", "extra_ref", "extra_label"):
            self.assertIn('name="%s"' % field_name, financing_tree)

    def test_tender_registration_fee_exposes_receipt_facts(self):
        bid = self.env["tender.bid"].create(
            {
                "tender_name": "Feedback Tender Registration",
                "project_id": self.project.id,
            }
        )
        purchase = self.env["tender.doc.purchase"].create(
            {
                "bid_id": bid.id,
                "amount": 500,
                "payment_method": "基本户转账缴纳",
                "receipt_partner_name": "中国石油天然气第七建设有限公司",
                "receipt_payee_name": "张三",
                "receipt_bank_name": "中国建设银行青岛市崂山支行",
                "receipt_bank_account": "37101986827051021071",
                "legacy_source_created_by": "段奕俊",
                "legacy_source_created_at": "2022-03-07 14:28:32",
            }
        )

        self.assertEqual(purchase.receipt_partner_name, "中国石油天然气第七建设有限公司")
        self.assertEqual(purchase.receipt_bank_account, "37101986827051021071")

        tree = self.env.ref("smart_construction_core.view_tender_doc_purchase_tree").arch_db
        form = self.env.ref("smart_construction_core.view_tender_doc_purchase_form").arch_db
        search = self.env.ref("smart_construction_core.view_tender_doc_purchase_search").arch_db
        bid_form = self.env.ref("smart_construction_core.view_tender_bid_form").arch_db

        for field_name in (
            "payment_method",
            "receipt_partner_name",
            "receipt_payee_name",
            "receipt_bank_name",
            "receipt_bank_account",
            "legacy_source_created_by",
            "legacy_source_created_at",
        ):
            self.assertIn('name="%s"' % field_name, tree)
            self.assertIn('name="%s"' % field_name, form)
            self.assertIn('name="%s"' % field_name, search)
        self.assertIn('name="receipt_partner_name"', bid_form)
        self.assertIn('name="receipt_bank_account"', bid_form)

    def test_construction_diary_list_exposes_projected_site_fields(self):
        tree = self.env.ref("smart_construction_core.view_sc_construction_diary_tree").arch_db

        for field_name in (
            "title",
            "category",
            "construction_unit",
            "project_manager",
            "weather",
        ):
            self.assertIn('name="%s"' % field_name, tree)
        self.assertIn('name="manpower_count" sum="现场人数"', tree)

    def test_rebuild_projection_lists_expose_source_and_audit_fields(self):
        ledger_tree = self.env.ref("smart_construction_core.view_sc_treasury_ledger_tree").arch_db
        ledger_form = self.env.ref("smart_construction_core.view_sc_treasury_ledger_form").arch_db
        dashboard_tree = self.env.ref("smart_construction_core.view_sc_dashboard_cockpit_fact_tree").arch_db
        workbench_tree = self.env.ref("smart_construction_core.view_sc_workbench_item_tree").arch_db
        material_tree = self.env.ref("smart_construction_core.view_sc_material_catalog_tree").arch_db

        for field_name in ("source_kind", "legacy_record_id", "legacy_source_ref"):
            self.assertIn('name="%s"' % field_name, ledger_tree)
            self.assertIn('name="%s"' % field_name, ledger_form)
        self.assertIn('name="amount" sum="金额合计"', ledger_tree)

        for field_name in ("document_no", "business_date", "requester_id", "handler_id"):
            self.assertIn('name="%s"' % field_name, dashboard_tree)
            self.assertIn('name="%s"' % field_name, workbench_tree)
        self.assertIn('name="quantity" sum="数量合计"', dashboard_tree)
        self.assertIn('name="tax_amount" sum="税额合计"', dashboard_tree)
        self.assertIn('name="due_date"', workbench_tree)

        for field_name in ("aux_uom_text", "depth", "short_pinyin", "active"):
            self.assertIn('name="%s"' % field_name, material_tree)

    def test_legacy_detail_lists_expose_source_and_amount_fields(self):
        expense_tree = self.env.ref("smart_construction_core.view_sc_expense_claim_tree").arch_db
        payment_line_tree = self.env.ref("smart_construction_core.view_payment_request_line_tree").arch_db
        payment_line_form = self.env.ref("smart_construction_core.view_payment_request_line_form").arch_db
        receipt_line_tree = self.env.ref("smart_construction_core.view_receipt_invoice_line_tree").arch_db
        receipt_line_form = self.env.ref("smart_construction_core.view_receipt_invoice_line_form").arch_db

        for field_name in (
            "payee",
            "payee_account",
            "payee_bank",
            "summary",
            "legacy_document_no",
            "legacy_document_state",
        ):
            self.assertIn('name="%s"' % field_name, expense_tree)
        self.assertIn('name="amount" sum="申请金额合计"', expense_tree)
        self.assertIn('name="approved_amount" sum="批准金额合计"', expense_tree)

        for field_name in (
            "source_document_no",
            "source_line_type",
            "source_counterparty_text",
            "source_contract_no",
        ):
            self.assertIn('name="%s"' % field_name, payment_line_tree)
            self.assertIn('name="%s"' % field_name, payment_line_form)
        self.assertIn('name="amount" sum="明细金额合计"', payment_line_tree)
        self.assertIn('name="current_pay_amount" sum="本次申请合计"', payment_line_tree)
        self.assertIn('name="legacy_line_id"', payment_line_form)
        self.assertIn('name="legacy_parent_id"', payment_line_form)
        self.assertIn('name="legacy_supplier_contract_id"', payment_line_form)

        for field_name in ("source_document_no", "source_table_name", "amount_source"):
            self.assertIn('name="%s"' % field_name, receipt_line_tree)
            self.assertIn('name="%s"' % field_name, receipt_line_form)
        self.assertIn('name="invoice_amount" sum="发票金额合计"', receipt_line_tree)
        self.assertIn('name="invoiced_before_amount" sum="历史已开票合计"', receipt_line_tree)
        self.assertIn('name="current_receipt_amount" sum="本次收款合计"', receipt_line_tree)
        self.assertIn('name="legacy_invoice_line_id"', receipt_line_form)
        self.assertIn('name="legacy_receipt_id"', receipt_line_form)
        self.assertIn('name="legacy_file_bill_id"', receipt_line_form)

    def test_material_outbound_and_settlement_lists_expose_business_totals(self):
        purchase_request_tree = self.env.ref("smart_construction_core.view_sc_material_purchase_request_tree").arch_db
        acceptance_tree = self.env.ref("smart_construction_core.view_sc_material_acceptance_tree").arch_db
        inbound_tree = self.env.ref("smart_construction_core.view_sc_material_inbound_tree").arch_db
        rfq_tree = self.env.ref("smart_construction_core.view_sc_material_rfq_tree").arch_db
        outbound_tree = self.env.ref("smart_construction_core.view_sc_material_outbound_tree").arch_db
        settlement_tree = self.env.ref("smart_construction_core.view_sc_material_settlement_tree").arch_db

        for arch in (purchase_request_tree, acceptance_tree, inbound_tree, rfq_tree):
            self.assertIn('name="legacy_fact_type"', arch)
        self.assertIn('name="purpose"', outbound_tree)
        self.assertIn('name="legacy_fact_type"', outbound_tree)
        self.assertIn('name="legacy_fact_type"', settlement_tree)
        self.assertIn('name="amount_untaxed" sum="未税金额合计"', settlement_tree)
        self.assertIn('name="tax_amount" sum="税额合计"', settlement_tree)
        self.assertIn('name="amount_total" sum="结算金额合计"', settlement_tree)

    def test_labor_equipment_subcontract_lists_expose_totals_and_source_type(self):
        attendance_tree = self.env.ref("smart_construction_core.view_sc_attendance_checkin_tree").arch_db
        labor_plan_tree = self.env.ref("smart_construction_core.view_sc_labor_plan_tree").arch_db
        labor_request_tree = self.env.ref("smart_construction_core.view_sc_labor_request_tree").arch_db
        labor_usage_tree = self.env.ref("smart_construction_core.view_sc_labor_usage_tree").arch_db
        labor_settlement_tree = self.env.ref("smart_construction_core.view_sc_labor_settlement_tree").arch_db
        labor_price_tree = self.env.ref("smart_construction_core.view_sc_labor_price_tree").arch_db
        equipment_plan_tree = self.env.ref("smart_construction_core.view_sc_equipment_plan_tree").arch_db
        equipment_request_tree = self.env.ref("smart_construction_core.view_sc_equipment_request_tree").arch_db
        equipment_usage_tree = self.env.ref("smart_construction_core.view_sc_equipment_usage_tree").arch_db
        equipment_settlement_tree = self.env.ref("smart_construction_core.view_sc_equipment_settlement_tree").arch_db
        equipment_price_tree = self.env.ref("smart_construction_core.view_sc_equipment_price_tree").arch_db
        subcontract_plan_tree = self.env.ref("smart_construction_core.view_sc_subcontract_plan_tree").arch_db
        subcontract_request_tree = self.env.ref("smart_construction_core.view_sc_subcontract_request_tree").arch_db
        subcontract_register_tree = self.env.ref("smart_construction_core.view_sc_subcontract_register_tree").arch_db
        subcontract_settlement_tree = self.env.ref("smart_construction_core.view_sc_subcontract_settlement_tree").arch_db
        subcontract_price_tree = self.env.ref("smart_construction_core.view_sc_subcontract_price_tree").arch_db

        self.assertIn('name="attendance_qty" sum="考勤人数合计"', attendance_tree)
        self.assertIn('name="work_hours" sum="工时合计"', attendance_tree)
        self.assertIn('name="worker_qty" sum="用工人数合计"', labor_usage_tree)
        self.assertIn('name="usage_qty" sum="使用台数合计"', equipment_usage_tree)
        for arch in (
            attendance_tree,
            labor_plan_tree,
            labor_request_tree,
            labor_usage_tree,
            labor_settlement_tree,
            labor_price_tree,
            equipment_plan_tree,
            equipment_request_tree,
            equipment_usage_tree,
            equipment_settlement_tree,
            equipment_price_tree,
            subcontract_plan_tree,
            subcontract_request_tree,
            subcontract_register_tree,
            subcontract_settlement_tree,
            subcontract_price_tree,
        ):
            self.assertIn('name="legacy_fact_type"', arch)

        for arch in (labor_settlement_tree, equipment_settlement_tree, subcontract_settlement_tree):
            self.assertIn('name="amount_untaxed" sum="未税金额合计"', arch)
            self.assertIn('name="tax_amount" sum="税额合计"', arch)
            self.assertIn('name="amount_total" sum="结算金额合计"', arch)

        self.assertIn('name="estimated_amount" sum="预计金额合计"', subcontract_plan_tree)
        self.assertIn('name="estimated_amount" sum="预计金额合计"', subcontract_request_tree)
        self.assertIn('name="registered_amount" sum="登记金额合计"', subcontract_register_tree)

    def test_plan_contract_quality_safety_lists_expose_source_type_and_totals(self):
        plan_tree = self.env.ref("smart_construction_core.view_sc_plan_tree").arch_db
        plan_form = self.env.ref("smart_construction_core.view_sc_plan_form").arch_db
        plan_report_tree = self.env.ref("smart_construction_core.view_sc_plan_report_tree").arch_db
        contract_event_tree = self.env.ref("smart_construction_core.view_sc_contract_event_tree").arch_db
        quality_standard_tree = self.env.ref("smart_construction_core.view_sc_check_standard_tree").arch_db
        quality_standard_form = self.env.ref("smart_construction_core.view_sc_check_standard_form").arch_db
        quality_issue_tree = self.env.ref("smart_construction_core.view_sc_quality_issue_tree").arch_db
        quality_rectification_tree = self.env.ref("smart_construction_core.view_sc_quality_rectification_tree").arch_db
        quality_recheck_tree = self.env.ref("smart_construction_core.view_sc_quality_recheck_tree").arch_db
        quality_recheck_form = self.env.ref("smart_construction_core.view_sc_quality_recheck_form").arch_db
        safety_plan_tree = self.env.ref("smart_construction_core.view_sc_safety_plan_tree").arch_db
        safety_plan_form = self.env.ref("smart_construction_core.view_sc_safety_plan_form").arch_db
        safety_disclosure_tree = self.env.ref("smart_construction_core.view_sc_safety_disclosure_tree").arch_db
        safety_disclosure_form = self.env.ref("smart_construction_core.view_sc_safety_disclosure_form").arch_db
        hazard_tree = self.env.ref("smart_construction_core.view_sc_hazard_source_tree").arch_db
        safety_issue_tree = self.env.ref("smart_construction_core.view_sc_safety_issue_tree").arch_db
        safety_issue_form = self.env.ref("smart_construction_core.view_sc_safety_issue_form").arch_db
        safety_rectification_tree = self.env.ref("smart_construction_core.view_sc_safety_rectification_tree").arch_db
        safety_recheck_tree = self.env.ref("smart_construction_core.view_sc_safety_recheck_tree").arch_db
        safety_recheck_form = self.env.ref("smart_construction_core.view_sc_safety_recheck_form").arch_db

        for arch in (
            plan_tree,
            plan_form,
            plan_report_tree,
            contract_event_tree,
            quality_standard_tree,
            quality_standard_form,
            quality_issue_tree,
            quality_rectification_tree,
            quality_recheck_tree,
            quality_recheck_form,
            safety_plan_tree,
            safety_plan_form,
            safety_disclosure_tree,
            safety_disclosure_form,
            hazard_tree,
            safety_issue_tree,
            safety_issue_form,
            safety_rectification_tree,
            safety_recheck_tree,
            safety_recheck_form,
        ):
            self.assertIn('name="legacy_fact_type"', arch)

        self.assertIn('name="amount_impact" sum="金额影响"', contract_event_tree)
        self.assertIn('name="tax_excluded_amount" sum="不含税金额"', contract_event_tree)
        self.assertIn('name="tax_amount" sum="税额"', contract_event_tree)
        self.assertIn('name="change_limit_amount" sum="变更控制上限"', contract_event_tree)

    def test_settlement_feedback_fields_are_real_business_fields(self):
        contract = self.env["construction.contract"].create(
            {
                "subject": "Feedback Income Contract",
                "type": "out",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "engineering_address": "Feedback Road 1",
            }
        )
        settlement = self.env["sc.settlement.order"].create(
            {
                "title": "Feedback Settlement Title",
                "project_id": self.project.id,
                "contract_id": contract.id,
                "partner_id": self.partner.id,
                "settlement_type": "in",
                "document_date": "2026-05-03",
                "submitted_amount": 120,
                "approved_amount": 100,
                "approved_date": "2026-05-04",
                "requested_fund_amount": 80,
                "settlement_description": "feedback settlement description",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "contract_id": contract.id,
                            "name": "settlement line",
                            "qty": 2,
                            "price_unit": 50,
                        },
                    )
                ],
            }
        )
        self.env["sc.settlement.adjustment"].create(
            {
                "settlement_id": settlement.id,
                "adjustment_type": "deduction",
                "state": "confirmed",
                "item_name": "扣款事项",
                "amount": 15,
            }
        )

        self.assertEqual(settlement.amount_total, 100)
        self.assertEqual(settlement.settlement_unit_id, self.partner)
        self.assertEqual(settlement.document_date.isoformat(), "2026-05-03")
        self.assertEqual(settlement.date_settlement.isoformat(), "2026-05-03")
        self.assertEqual(settlement.approved_date.isoformat(), "2026-05-04")
        self.assertEqual(settlement.final_approved_date.isoformat(), "2026-05-04")
        self.assertEqual(settlement.contract_subject, "Feedback Income Contract")
        self.assertEqual(settlement.engineering_address, "Feedback Road 1")
        self.assertEqual(settlement.deduction_amount, 15)
        self.assertEqual(settlement.unpaid_amount, 100)
        self.assertEqual(settlement.employer_name, self.partner.display_name)
        self.assertEqual(settlement.contractor_name, self.env.company.partner_id.display_name)

        tree = self.env.ref("smart_construction_core.view_sc_settlement_order_tree").arch_db
        self.assertIn('name="contract_subject"', tree)
        self.assertIn('name="contract_total_amount" sum="合同总额合计"', tree)
        self.assertIn('name="submitted_amount" sum="送审金额合计"', tree)
        self.assertIn('name="approved_amount" sum="审定金额合计"', tree)
        self.assertIn('name="requested_fund_amount" sum="申请资金金额合计"', tree)
        self.assertIn('name="engineering_address"', tree)

    def test_currency_defaults_to_cny_and_is_hidden_from_business_views(self):
        cny = self.env.ref("base.CNY")
        self.assertEqual(self.env.company.currency_id, cny)

        views = self.env["ir.ui.view"].search([("arch_db", "ilike", 'name="currency_id"')])
        visible_hits = []
        for view in views:
            if view.xml_id and not view.xml_id.startswith("smart_construction_core."):
                continue
            for match in re.finditer(r'<field[^>]+name="currency_id"[^>]*/>', view.arch_db or ""):
                if 'invisible="1"' not in match.group(0):
                    visible_hits.append("%s: %s" % (view.xml_id or view.name, match.group(0)))
        self.assertFalse(visible_hits, "\n".join(visible_hits))

    def test_material_rental_models_cover_plan_contract_supplier_and_payment(self):
        supplier = self.env["res.partner"].create({"name": "Rental Supplier", "supplier_rank": 1})
        contract = self.env["construction.contract"].create(
            {
                "name": "Rental Contract",
                "subject": "周转材料租赁合同",
                "type": "in",
                "project_id": self.project.id,
                "partner_id": supplier.id,
            }
        )
        plan = self.env["sc.material.rental.plan"].create(
            {
                "project_id": self.project.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "rent_purpose": "脚手架周转",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "钢管",
                            "material_spec": "48mm",
                            "unit_name": "米",
                            "planned_qty": 10,
                            "planned_days": 5,
                            "daily_price": 2,
                        },
                    )
                ],
            }
        )
        order = self.env["sc.material.rental.order"].create(
            {
                "project_id": self.project.id,
                "plan_id": plan.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "钢管",
                            "qty": 10,
                            "rental_days": 5,
                            "daily_price": 2,
                        },
                    )
                ],
            }
        )
        payment = self.env["payment.request"].create(
            {
                "type": "pay",
                "project_id": self.project.id,
                "partner_id": supplier.id,
                "contract_id": contract.id,
                "amount": 100,
            }
        )
        settlement = self.env["sc.material.rental.settlement"].create(
            {
                "project_id": self.project.id,
                "rental_order_id": order.id,
                "supplier_id": supplier.id,
                "contract_id": contract.id,
                "payment_request_id": payment.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "material_name": "钢管",
                            "qty": 10,
                            "rental_days": 5,
                            "daily_price": 2,
                            "damage_amount": 8,
                        },
                    )
                ],
            }
        )

        self.assertEqual(plan.estimated_amount, 100)
        self.assertEqual(order.amount_total, 100)
        self.assertEqual(settlement.rent_amount, 100)
        self.assertEqual(settlement.damage_amount, 8)
        self.assertEqual(settlement.amount_total, 108)
        self.assertEqual(settlement.payment_request_id, payment)

        for xmlid in (
            "smart_construction_core.view_sc_material_rental_plan_tree",
            "smart_construction_core.view_sc_material_rental_order_tree",
            "smart_construction_core.view_sc_material_rental_settlement_tree",
        ):
            arch = self.env.ref(xmlid).arch_db
            self.assertIn('name="contract_id"', arch)
            self.assertIn('name="supplier_id"', arch)
            self.assertIn('name="currency_id" invisible="1"', arch)

        self.assertEqual(self.env.ref("smart_construction_core.menu_sc_material_rental_group").name, "周转材料租赁")

    def test_deposit_feedback_fields_and_contract_amount_label_are_business_ready(self):
        tree = self.env.ref("smart_construction_core.view_sc_expense_claim_tree").arch_db
        form = self.env.ref("smart_construction_core.view_sc_expense_claim_form").arch_db
        contract_field = self.env["construction.contract"]._fields["line_amount_total"]

        for field_name in (
            "guarantee_project_name",
            "guarantee_type",
            "payment_method",
            "payer_account",
            "company_name_text",
            "clearing_method",
            "return_reason",
            "is_returned",
        ):
            self.assertIn('name="%s"' % field_name, tree + form)
        self.assertEqual(contract_field.string, "最终合同价")

    def test_repayment_registration_is_inflow_business_entry(self):
        action = self.env.ref("smart_construction_core.action_sc_expense_claim_repayment_registration")
        claim = self.env["sc.expense.claim"].create(
            {
                "claim_type": "project_company_repay",
                "expense_type": "还款登记",
                "summary": "还款登记",
                "project_id": self.project.id,
                "amount": 1200,
            }
        )

        self.assertEqual(claim.direction, "inflow")
        self.assertIn("project_company_repay", action.domain)
        self.assertIn("'search_default_inflow': 1", action.context)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_expense_claim_tree").active)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_financing_loan_tree").active)
