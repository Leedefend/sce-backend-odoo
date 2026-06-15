# -*- coding: utf-8 -*-
import inspect
import re

from odoo.exceptions import UserError
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
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
        self.assertNotIn("'active_test': False", action.context)
        self.assertIn('name="sc_supplier_type_label"', tree.arch_db)
        self.assertIn('name="sc_supplier_type_ids"', form.arch_db)
        self.assertNotIn('name="legacy_partner_id"', tree.arch_db)
        self.assertNotIn('name="legacy_partner_source"', tree.arch_db)
        self.assertNotIn('name="legacy_partner_name"', form.arch_db)
        self.assertNotIn('name="legacy_deleted_flag"', search.arch_db)

    def test_customer_and_supplier_entries_expose_business_handling_fields(self):
        customer_action = self.env.ref("smart_construction_core.action_sc_customer_partner")
        customer_tree = self.env.ref("smart_construction_core.view_sc_customer_partner_tree")
        customer_form = self.env.ref("smart_construction_core.view_sc_customer_partner_form")
        customer_search = self.env.ref("smart_construction_core.view_sc_customer_partner_search")
        supplier_action = self.env.ref("smart_construction_core.action_sc_supplier_partner")
        supplier_tree = self.env.ref("smart_construction_core.view_sc_supplier_partner_tree")
        supplier_form = self.env.ref("smart_construction_core.view_sc_supplier_partner_form")
        supplier_search = self.env.ref("smart_construction_core.view_sc_supplier_partner_search")

        self.assertIn("'default_customer_rank': 1", customer_action.context)
        self.assertIn("'default_company_type': 'company'", customer_action.context)
        self.assertNotIn("'active_test': False", customer_action.context)
        self.assertIn("'default_supplier_rank': 1", supplier_action.context)
        self.assertNotIn("'active_test': False", supplier_action.context)
        for arch in (customer_tree.arch_db, supplier_tree.arch_db):
            self.assertIn('name="active"', arch)
            self.assertIn('name="user_id"', arch)
            self.assertIn('name="category_id"', arch)
            self.assertIn('name="comment"', arch)
            self.assertIn('name="sc_bank_name"', arch)
            self.assertIn('name="sc_bank_account"', arch)
            self.assertIn('name="sc_supplier_type_label"', arch)
            self.assertIn('name="street"', arch)
            self.assertIn('name="sc_business_scope"', arch)
            self.assertIn('name="sc_source_document_state"', arch)
            self.assertIn('name="sc_source_push_result"', arch)
            self.assertIn('name="sc_source_project_name"', arch)
            self.assertIn('name="sc_source_partner_code"', arch)
            self.assertIn('name="sc_source_cooperation_type"', arch)
            self.assertIn('name="sc_source_receipt_amount"', arch)
            self.assertIn('name="sc_source_payment_amount"', arch)
            self.assertIn('name="sc_default_tax_rate_text"', arch)
            self.assertIn('name="sc_source_created_by"', arch)
            self.assertLess(arch.index('name="name"'), arch.index('name="sc_source_document_state"'))
            self.assertIn('name="sc_source_created_at"', arch)
            self.assertIn('name="sc_business_role_label"', arch)
            self.assertIn('name="sc_business_fact_basis"', arch)
        self.assertNotIn('name="sc_supplier_type"', customer_tree.arch_db)
        for arch in (customer_form.arch_db, supplier_form.arch_db):
            self.assertIn('name="child_ids"', arch)
            self.assertIn('name="bank_ids"', arch)
            self.assertIn('name="sc_attachment_ids"', arch)
            self.assertIn('name="action_open_sc_partner_business_fact_lines"', arch)
            self.assertIn('name="sc_business_fact_line_ids"', arch)
            self.assertIn('name="comment"', arch)
            self.assertIn('name="active"', arch)
            self.assertIn('name="category_id"', arch)
            self.assertIn('name="user_id"', arch)
            self.assertIn('name="property_account_position_id"', arch)
            self.assertIn('string="业务信息"', arch)
            self.assertIn('string="关联业务明细"', arch)
            self.assertIn('name="action_open_source_record"', arch)
            self.assertIn('name="sc_source_fact_count" string="关联业务数" readonly="1"', arch)
            self.assertIn('name="sc_source_fact_source"', arch)
            self.assertIn('name="sc_source_receipt_amount" string="收款金额" readonly="1"', arch)
            self.assertIn('name="sc_source_payment_amount" string="付款金额" readonly="1"', arch)
            self.assertIn('name="sc_supplier_type_label"', arch)
        self.assertIn('name="company_type" string="客户类型"', customer_tree.arch_db)
        for label in ("客户身份", "企业资质", "联系与地址", "账户与开票", "业务画像"):
            self.assertIn('string="%s"' % label, customer_form.arch_db)
        self.assertIn('name="company_type" string="客户类型"', customer_form.arch_db)
        self.assertIn('name="property_account_receivable_id"', customer_form.arch_db)
        for arch in (customer_search.arch_db, supplier_search.arch_db):
            self.assertIn('name="phone"', arch)
            self.assertIn('name="mobile"', arch)
            self.assertIn('name="email"', arch)
            self.assertIn('name="sc_bank_name"', arch)
            self.assertIn('name="sc_bank_account"', arch)
            self.assertIn('name="sc_supplier_type_label"', arch)
            self.assertIn('name="street"', arch)
            self.assertIn('name="sc_business_scope"', arch)
            self.assertIn('name="sc_source_partner_code"', arch)
            self.assertIn('name="sc_source_document_state"', arch)
            self.assertIn('name="sc_source_push_result"', arch)
            self.assertIn('name="sc_source_project_name"', arch)
            self.assertIn('name="sc_source_cooperation_type"', arch)
            self.assertIn('name="sc_source_created_by"', arch)
            self.assertIn('name="sc_business_role_label"', arch)
            self.assertIn('name="sc_business_fact_basis"', arch)
            self.assertIn('name="category_id"', arch)
            self.assertIn('name="user_id"', arch)
            self.assertIn('name="active"', arch)
            self.assertIn('name="comment"', arch)
        self.assertIn('name="property_payment_term_id"', customer_form.arch_db)
        self.assertIn('name="property_supplier_payment_term_id"', supplier_form.arch_db)
        self.assertIn('name="customer_inactive"', customer_search.arch_db)
        self.assertIn('name="supplier_inactive"', supplier_search.arch_db)
        self.assertIn('name="group_user"', customer_search.arch_db)
        self.assertIn('name="group_user"', supplier_search.arch_db)

    def test_formal_partner_entries_hide_migration_evidence_fields(self):
        formal_views = [
            self.env.ref("smart_construction_core.view_sc_customer_partner_tree"),
            self.env.ref("smart_construction_core.view_sc_customer_partner_form"),
            self.env.ref("smart_construction_core.view_sc_customer_partner_search"),
            self.env.ref("smart_construction_core.view_sc_supplier_partner_tree"),
            self.env.ref("smart_construction_core.view_sc_supplier_partner_form"),
            self.env.ref("smart_construction_core.view_sc_supplier_partner_search"),
        ]
        migration_evidence_fields = (
            "legacy_partner_id",
            "legacy_partner_source",
            "legacy_partner_name",
            "legacy_credit_code",
            "legacy_tax_no",
            "legacy_deleted_flag",
            "legacy_source_evidence",
            "sc_legacy_source_label",
            "sc_legacy_external_id",
            "sc_legacy_partner_source",
            "sc_legacy_partner_id",
            "sc_import_batch",
            "sc_source_evidence",
        )

        for view in formal_views:
            for field_name in migration_evidence_fields:
                self.assertNotIn('name="%s"' % field_name, view.arch_db, msg="%s leaked in %s" % (field_name, view.name))

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
        supplier = self.env["res.partner"].create({"name": "Feedback Expenditure Supplier", "is_company": True})
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

        detail_model = self.env["sc.partner.business.fact.line"]
        receipt_lines = detail_model.search([("partner_id", "=", receipt_customer.id)])
        supplier_lines = detail_model.search([("partner_id", "=", supplier.id)])
        self.assertTrue(receipt_lines.filtered(lambda line: line.source_label == "收款事实" and line.amount == 123))
        self.assertTrue(supplier_lines.filtered(lambda line: line.source_label == "付款申请" and line.amount == 456))
        detail_action = receipt_customer.action_open_sc_partner_business_fact_lines()
        self.assertEqual(detail_action["id"], self.env.ref("smart_construction_core.action_sc_partner_business_fact_line").id)
        self.assertEqual(detail_action["domain"], [("partner_id", "=", receipt_customer.id)])

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

    def test_tender_optional_scope_metadata_is_non_blocking(self):
        bid = self.env["tender.bid"].create(
            {
                "tender_name": "Feedback Tender Optional Scope",
                "project_id": self.project.id,
            }
        )

        self.assertFalse(bid.business_scope_key)
        self.assertFalse(bid.business_direction)
        self.assertFalse(bid.carrier_type)
        self.assertFalse(bid.carrier_model)
        self.assertEqual(bid.carrier_res_id, 0)

        bid.write(
            {
                "business_scope_key": "income:feedback",
                "business_direction": "income",
                "carrier_type": "project",
                "carrier_model": "project.project",
                "carrier_res_id": self.project.id,
            }
        )
        self.assertEqual(bid.project_id, self.project)
        self.assertEqual(bid.business_direction, "income")
        self.assertEqual(bid.carrier_model, "project.project")

        bid_form = self.env.ref("smart_construction_core.view_tender_bid_form").arch_db
        self.assertIn('name="platform_scope_metadata"', bid_form)
        for field_name in (
            "business_scope_key",
            "business_direction",
            "carrier_type",
            "carrier_model",
            "carrier_res_id",
        ):
            self.assertIn('name="%s"' % field_name, bid_form)

    def test_tender_registration_form_exposes_business_workflow_buttons(self):
        bid_form = self.env.ref("smart_construction_core.view_tender_bid_form").arch_db

        for button_name in (
            "action_to_estimating",
            "action_to_submitted",
            "action_to_waiting",
            "action_mark_won",
            "action_mark_lost",
            "action_to_prepare",
        ):
            self.assertIn('name="%s"' % button_name, bid_form)

    def test_tender_registration_business_workflow_reaches_won_contract(self):
        bid = self.env["tender.bid"].create(
            {
                "tender_name": "Feedback Tender Workflow",
                "project_id": self.project.id,
                "owner_id": self.partner.id,
                "bid_amount": 1200.0,
            }
        )

        bid.action_to_estimating()
        self.assertEqual(bid.state, "estimating")
        bid.action_to_submitted()
        self.assertEqual(bid.state, "submitted")
        bid.action_to_waiting()
        self.assertEqual(bid.state, "waiting")
        bid.action_mark_won()

        self.assertEqual(bid.state, "won")
        self.assertTrue(bid.contract_id)
        self.assertEqual(bid.contract_id.project_id, self.project)
        self.assertEqual(bid.contract_id.partner_id, self.partner)
        self.assertEqual(bid.contract_id.subject, "Feedback Tender Workflow")

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

        for field_name in (
            "source_document_no",
            "source_table_name",
            "amount_source",
            "invoice_date",
            "invoice_document_no",
            "invoice_document_state",
            "surcharge_amount",
        ):
            self.assertIn('name="%s"' % field_name, receipt_line_tree)
            self.assertIn('name="%s"' % field_name, receipt_line_form)
        self.assertIn('name="invoice_amount" sum="发票金额合计"', receipt_line_tree)
        self.assertIn('name="surcharge_amount" sum="附加税合计"', receipt_line_tree)
        self.assertIn('name="invoiced_before_amount" sum="历史已开票合计"', receipt_line_tree)
        self.assertIn('name="current_receipt_amount" sum="本次收款合计"', receipt_line_tree)
        self.assertIn('name="legacy_invoice_line_id"', receipt_line_form)
        self.assertIn('name="legacy_receipt_id"', receipt_line_form)
        self.assertIn('name="legacy_file_bill_id"', receipt_line_form)

    def test_output_invoice_menu_uses_detail_invoice_fact_model(self):
        action = self.env.ref("smart_construction_core.action_sc_invoice_output")
        self.assertEqual(action.res_model, "sc.output.invoice.ledger")
        self.assertEqual(action.search_view_id, self.env.ref("smart_construction_core.view_output_invoice_ledger_search"))
        self.assertIn("search_default_group_by_project_id", action.context)

    def test_output_invoice_adjustment_menu_uses_signed_adjustment_domain(self):
        action = self.env.ref("smart_construction_core.action_sc_output_invoice_adjustment")
        menu = self.env.ref("smart_construction_core.menu_sc_output_invoice_adjustment")

        self.assertEqual(action.name, "销项调整记录")
        self.assertEqual(action.res_model, "sc.output.invoice.ledger")
        self.assertEqual(action.search_view_id, self.env.ref("smart_construction_core.view_output_invoice_ledger_search"))
        self.assertIn("signed_adjustment", action.domain)
        self.assertIn("search_default_signed_adjustment", action.context)
        self.assertEqual(menu.action, action)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_change_registration_menu_is_operational_entry(self):
        action = self.env.ref("smart_construction_core.action_sc_output_invoice_change_registration")
        menu = self.env.ref("smart_construction_core.menu_sc_output_invoice_change_registration")

        self.assertEqual(action.name, "销项变更登记")
        self.assertEqual(action.res_model, "sc.output.invoice.adjustment")
        self.assertEqual(action.search_view_id, self.env.ref("smart_construction_core.view_sc_output_invoice_adjustment_search"))
        self.assertEqual(menu.action, action)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_adjustment_ledger_scope_includes_runtime_red_flush(self):
        from odoo.addons.smart_construction_core.models.core.output_invoice_ledger import ScOutputInvoiceLedger

        init_source = inspect.getsource(ScOutputInvoiceLedger.init)
        self.assertIn("ir.red_flush_adjustment_id IS NOT NULL", init_source)
        self.assertIn("ir.legacy_source_model = 'sc.legacy.invoice.tax.fact'", init_source)
        self.assertIn("ir.legacy_source_table = 'C_JXXP_XXKPDJ'", init_source)
        self.assertIn("legacy_output_invoice_registration", init_source)
        self.assertIn("FROM sc_invoice_registration ir2", init_source)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_ledger_includes_positive_legacy_output_tax_fact_without_receipt_duplicate(self):
        positive = self.env["sc.invoice.registration"].create(
            {
                "source_origin": "legacy",
                "source_kind": "output_invoice_tax",
                "direction": "output",
                "state": "legacy_confirmed",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "document_no": "XXKPDJ-POSITIVE-LEGACY",
                "invoice_no": "INV-POSITIVE-LEGACY",
                "amount_no_tax": 100.0,
                "tax_amount": 9.0,
                "amount_total": 109.0,
                "legacy_source_model": "sc.legacy.invoice.tax.fact",
                "legacy_source_table": "C_JXXP_XXKPDJ",
                "legacy_record_id": "positive-output-tax-fact-smoke",
            }
        )

        ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.invoice.registration"), ("source_record_id", "=", positive.id)],
            limit=1,
        )
        self.assertTrue(ledger)
        self.assertEqual(ledger.adjustment_kind, "normal")
        self.assertEqual(ledger.amount_source, "legacy_output_invoice_registration")
        self.assertEqual(ledger.invoice_amount, 109.0)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_ledger_prefers_registration_fact_over_receipt_invoice_line(self):
        request = self.env["payment.request"].create(
            {
                "name": "FB-RECEIPT-WITH-OUTPUT-REGISTRATION",
                "type": "receive",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 50.0,
            }
        )
        receipt_line = self.env["sc.receipt.invoice.line"].create(
            {
                "request_id": request.id,
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "legacy_invoice_line_id": "registration-first-line",
                "legacy_receipt_id": "registration-first-receipt",
                "invoice_no": "INV-REGISTRATION-FIRST",
                "invoice_issue_company": "Feedback Issue Company",
                "invoice_party_name": "Feedback Party",
                "invoice_amount": 50.0,
                "surcharge_amount": 0.5,
            }
        )
        registration = self.env["sc.invoice.registration"].create(
            {
                "source_origin": "legacy",
                "source_kind": "output_invoice_tax",
                "direction": "output",
                "state": "legacy_confirmed",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "document_no": "XXKPDJ-REGISTRATION-FIRST",
                "invoice_no": "INV-REGISTRATION-FIRST",
                "amount_no_tax": 90.0,
                "tax_amount": 9.0,
                "amount_total": 99.0,
                "legacy_source_model": "sc.legacy.invoice.tax.fact",
                "legacy_source_table": "C_JXXP_XXKPDJ",
                "legacy_record_id": "registration-first-output-tax-fact",
            }
        )

        receipt_ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.receipt.invoice.line"), ("source_record_id", "=", receipt_line.id)],
            limit=1,
        )
        registration_ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.invoice.registration"), ("source_record_id", "=", registration.id)],
            limit=1,
        )
        self.assertFalse(receipt_ledger)
        self.assertTrue(registration_ledger)
        self.assertEqual(registration_ledger.invoice_document_no, "XXKPDJ-REGISTRATION-FIRST")
        self.assertEqual(registration_ledger.invoice_amount, 99.0)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_ledger_exposes_signed_adjustment_filters(self):
        ledger_tree = self.env.ref("smart_construction_core.view_output_invoice_ledger_tree").arch_db
        ledger_search = self.env.ref("smart_construction_core.view_output_invoice_ledger_search").arch_db

        self.assertIn('decoration-danger="adjustment_kind == \'signed_adjustment\'"', ledger_tree)
        for field_name in (
            "adjustment_kind",
            "invoice_amount",
            "amount_no_tax",
            "tax_amount",
            "surcharge_amount",
            "invoice_document_no",
            "source_table_name",
            "receipt_line_count",
        ):
            self.assertIn('name="%s"' % field_name, ledger_tree)
        self.assertIn('name="negative_amount"', ledger_search)
        self.assertIn('name="signed_adjustment"', ledger_search)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_red_flush_registration_generates_negative_output_invoice(self):
        request = self.env["payment.request"].create(
            {
                "name": "FB-RECEIPT-RED-FLUSH",
                "type": "receive",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 109.0,
            }
        )
        receipt_line = self.env["sc.receipt.invoice.line"].create(
            {
                "request_id": request.id,
                "legacy_invoice_line_id": "red-flush-line",
                "legacy_receipt_id": "red-flush-receipt",
                "invoice_no": "INV-RED-001",
                "invoice_issue_company": "Feedback Issue Company",
                "invoice_party_name": "Feedback Party",
                "invoice_amount": 109.0,
                "surcharge_amount": 1.2,
            }
        )
        ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.receipt.invoice.line"), ("source_record_id", "=", receipt_line.id)],
            limit=1,
        )
        self.assertTrue(ledger)

        adjustment = self.env["sc.output.invoice.adjustment"].create(
            {
                "original_ledger_id": ledger.id,
                "red_flush_invoice_no": "INV-RED-001-R",
                "reason": "用户反馈红冲闭环验证",
            }
        )
        adjustment.action_confirm()

        generated = adjustment.generated_invoice_id
        self.assertTrue(generated)
        self.assertEqual(adjustment.state, "confirmed")
        self.assertEqual(generated.red_flush_adjustment_id, adjustment)
        self.assertEqual(generated.direction, "output")
        self.assertEqual(generated.source_kind, "output_invoice_tax")
        self.assertEqual(generated.state, "registered")
        self.assertEqual(generated.invoice_no, "INV-RED-001-R")
        self.assertEqual(generated.amount_total, -109.0)
        self.assertEqual(generated.amount_no_tax, -109.0)
        self.assertEqual(generated.tax_amount, 0.0)
        self.assertEqual(generated.surcharge_amount, -1.2)

        red_ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.invoice.registration"), ("source_record_id", "=", generated.id)],
            limit=1,
        )
        self.assertTrue(red_ledger)
        self.assertEqual(red_ledger.adjustment_kind, "signed_adjustment")
        self.assertEqual(red_ledger.invoice_amount, -109.0)

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_red_flush_blocks_same_invoice_no(self):
        request = self.env["payment.request"].create(
            {
                "name": "FB-RECEIPT-RED-FLUSH-BLOCK",
                "type": "receive",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 109.0,
            }
        )
        receipt_line = self.env["sc.receipt.invoice.line"].create(
            {
                "request_id": request.id,
                "legacy_invoice_line_id": "red-flush-line-block",
                "legacy_receipt_id": "red-flush-receipt-block",
                "invoice_no": "INV-RED-BLOCK-001",
                "invoice_issue_company": "Feedback Issue Company",
                "invoice_party_name": "Feedback Party",
                "invoice_amount": 109.0,
            }
        )
        ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.receipt.invoice.line"), ("source_record_id", "=", receipt_line.id)],
            limit=1,
        )
        adjustment = self.env["sc.output.invoice.adjustment"].create(
            {
                "original_ledger_id": ledger.id,
                "red_flush_invoice_no": "INV-RED-BLOCK-001",
            }
        )

        with self.assertRaises(UserError):
            adjustment.action_confirm()
        adjustment.invalidate_recordset()
        self.assertEqual(adjustment.state, "draft")

    @tagged("post_install", "-at_install", "user_feedback", "output_invoice_red_flush")
    def test_output_invoice_red_flush_blocks_invalid_state_jump_or_late_cancel(self):
        request = self.env["payment.request"].create(
            {
                "name": "FB-RECEIPT-RED-FLUSH-STATE",
                "type": "receive",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 109.0,
            }
        )
        receipt_line = self.env["sc.receipt.invoice.line"].create(
            {
                "request_id": request.id,
                "legacy_invoice_line_id": "red-flush-line-state",
                "legacy_receipt_id": "red-flush-receipt-state",
                "invoice_no": "INV-RED-STATE-001",
                "invoice_issue_company": "Feedback Issue Company",
                "invoice_party_name": "Feedback Party",
                "invoice_amount": 109.0,
            }
        )
        ledger = self.env["sc.output.invoice.ledger"].search(
            [("source_model", "=", "sc.receipt.invoice.line"), ("source_record_id", "=", receipt_line.id)],
            limit=1,
        )
        adjustment = self.env["sc.output.invoice.adjustment"].create(
            {
                "original_ledger_id": ledger.id,
                "red_flush_invoice_no": "INV-RED-STATE-001-R",
            }
        )

        adjustment.action_confirm()
        adjustment.invalidate_recordset()
        self.assertEqual(adjustment.state, "confirmed")
        with self.assertRaises(UserError):
            adjustment.action_confirm()
        with self.assertRaises(UserError):
            adjustment.action_cancel()

        cancel_adjustment = self.env["sc.output.invoice.adjustment"].create(
            {
                "original_ledger_id": ledger.id,
                "red_flush_invoice_no": "INV-RED-STATE-001-CANCEL",
            }
        )
        cancel_adjustment.action_cancel()
        cancel_adjustment.invalidate_recordset()
        self.assertEqual(cancel_adjustment.state, "cancel")
        with self.assertRaises(UserError):
            cancel_adjustment.action_confirm()
        with self.assertRaises(UserError):
            cancel_adjustment.action_cancel()

    def test_invoice_registration_accepts_signed_legacy_adjustment_amounts(self):
        invoice = self.env["sc.invoice.registration"].create(
            {
                "name": "LEGACY-RED-INVOICE",
                "source_origin": "legacy",
                "source_kind": "output_invoice_tax",
                "direction": "output",
                "state": "legacy_confirmed",
                "project_id": self.project.id,
                "amount_no_tax": -100.0,
                "tax_amount": -9.0,
                "amount_total": -109.0,
                "surcharge_amount": -1.2,
                "legacy_source_model": "sc.legacy.invoice.tax.fact",
                "legacy_record_id": "signed-adjustment-smoke",
            }
        )

        self.assertEqual(invoice.amount_total, -109.0)
        self.assertEqual(invoice.tax_amount, -9.0)
        self.assertEqual(invoice.surcharge_amount, -1.2)

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
        self.assertEqual(contract_field.string, "合同明细合计")

    def test_expense_claim_exposes_handling_and_anchor_policy(self):
        tree = self.env.ref("smart_construction_core.view_sc_expense_claim_tree").arch_db
        form = self.env.ref("smart_construction_core.view_sc_expense_claim_form").arch_db
        search = self.env.ref("smart_construction_core.view_sc_expense_claim_search").arch_db
        claim = self.env["sc.expense.claim"].create(
            {
                "source_origin": "legacy",
                "claim_type": "deposit_receive",
                "expense_type": "自筹保证金",
                "summary": "自筹保证金",
                "project_id": self.project.id,
                "amount": 1000,
                "state": "legacy_confirmed",
            }
        )

        for field_name in ("business_axis", "handling_kind", "financial_flow", "payment_anchor_policy"):
            self.assertIn('name="%s"' % field_name, tree + form + search)
        self.assertEqual(claim.business_axis, "guarantee")
        self.assertEqual(claim.handling_kind, "self_funding_deposit")
        self.assertEqual(claim.financial_flow, "cash_in")
        self.assertEqual(claim.payment_anchor_policy, "legacy_optional")

    def test_legacy_self_funding_fact_projects_to_formal_registration(self):
        category = self.env.ref("smart_construction_core.business_category_finance_self_funding_refund")
        legacy = self.env["sc.legacy.self.funding.fact"].create(
            {
                "source_table": "unit_legacy_self_funding_refund",
                "legacy_record_id": "refund-001",
                "line_type": "refund",
                "document_no": "LEG-SF-REFUND-001",
                "document_date": "2026-06-01",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "partner_name": self.partner.name,
                "refund_amount": 123.45,
                "account_name": "历史账户",
                "note": "历史自筹退回回放测试",
            }
        )

        first = self.env["sc.self.funding.registration"].project_legacy_self_funding_facts()
        second = self.env["sc.self.funding.registration"].project_legacy_self_funding_facts()
        projected = self.env["sc.self.funding.registration"].search(
            [
                ("legacy_source_table", "=", legacy.source_table),
                ("legacy_record_id", "=", legacy.legacy_record_id),
                ("funding_type", "=", "refund"),
            ]
        )

        self.assertEqual(len(projected), 1)
        self.assertGreaterEqual(first.get("created"), 1)
        self.assertGreaterEqual(second.get("skipped_existing"), 1)
        self.assertEqual(projected.source_origin, "legacy")
        self.assertEqual(projected.state, "done")
        self.assertEqual(projected.business_category_id, category)
        self.assertEqual(projected.amount, 123.45)

    def test_deduction_cash_flow_drives_payment_request_type(self):
        receive_request = self.env["payment.request"].create(
            {
                "name": "Deduction Paid Receive Request",
                "type": "receive",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
            }
        )
        pay_request = self.env["payment.request"].create(
            {
                "name": "Deduction Refund Pay Request",
                "type": "pay",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
            }
        )
        deduction_paid = self.env["sc.expense.claim"].create(
            {
                "claim_type": "expense",
                "expense_type": "扣款实缴登记",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "payment_request_id": receive_request.id,
                "payment_account_name": "公司收款账户",
                "amount": 100,
            }
        )
        deduction_refund = self.env["sc.expense.claim"].create(
            {
                "claim_type": "deduction_refund",
                "expense_type": "扣款实缴退回",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "payment_request_id": pay_request.id,
                "payee": self.partner.name,
                "payment_account_name": "公司付款账户",
                "amount": 100,
            }
        )

        self.assertEqual(deduction_paid.financial_flow, "cash_in")
        self.assertEqual(deduction_paid.payment_anchor_policy, "receive_request_required")
        deduction_paid._check_business_ready()
        self.assertEqual(deduction_refund.financial_flow, "cash_out")
        self.assertEqual(deduction_refund.payment_anchor_policy, "pay_request_required")
        deduction_refund._check_business_ready()
        deduction_paid.payment_request_id = pay_request
        with self.assertRaises(UserError):
            deduction_paid._check_business_ready()

    def test_expense_claim_formal_actions_use_business_filters_not_financial_flow(self):
        expected_contexts = {
            "smart_construction_core.action_sc_expense_claim_deduction_bill": "search_default_deduction_bill",
            "smart_construction_core.action_sc_expense_claim_deduction_paid": "search_default_deduction_paid",
            "smart_construction_core.action_sc_expense_claim_deduction_paid_refund": "search_default_deduction_refund",
            "smart_construction_core.action_sc_expense_claim_repayment_registration": "search_default_repayment_registration",
            "smart_construction_core.action_sc_expense_claim_contractor_project_repay": "search_default_repayment_contractor_project",
            "smart_construction_core.action_sc_expense_claim_project_repay_company": "search_default_repayment_project_company",
        }

        for action_xmlid, search_key in expected_contexts.items():
            context = self.env.ref(action_xmlid).context
            self.assertIn("'%s': 1" % search_key, context)
            self.assertNotIn("'search_default_inflow': 1", context)
            self.assertNotIn("'search_default_outflow': 1", context)
            self.assertNotIn("'search_default_finance_noncash': 1", context)
            self.assertNotIn("'search_default_finance_cash_in': 1", context)
            self.assertNotIn("'search_default_finance_cash_out': 1", context)
            self.assertNotIn("'search_default_finance_interfund': 1", context)

    def test_expense_claim_formal_actions_use_dedicated_search_and_list_views(self):
        deduction_search = self.env.ref("smart_construction_core.view_sc_expense_claim_deduction_search")
        deduction_tree = self.env.ref("smart_construction_core.view_sc_expense_claim_deduction_registration_tree")
        deduction_cash_tree = self.env.ref("smart_construction_core.view_sc_expense_claim_deduction_cash_tree")
        repayment_search = self.env.ref("smart_construction_core.view_sc_expense_claim_repayment_search")
        repayment_tree = self.env.ref("smart_construction_core.view_sc_expense_claim_repayment_tree")

        expected = {
            "smart_construction_core.action_sc_expense_claim_deduction_bill": (deduction_search, deduction_tree),
            "smart_construction_core.action_sc_expense_claim_deduction_paid": (deduction_search, deduction_cash_tree),
            "smart_construction_core.action_sc_expense_claim_deduction_paid_refund": (deduction_search, deduction_cash_tree),
            "smart_construction_core.action_sc_expense_claim_repayment_registration": (repayment_search, repayment_tree),
            "smart_construction_core.action_sc_expense_claim_contractor_project_repay": (repayment_search, repayment_tree),
            "smart_construction_core.action_sc_expense_claim_project_repay_company": (repayment_search, repayment_tree),
        }

        for action_xmlid, (search, tree) in expected.items():
            action = self.env.ref(action_xmlid)
            self.assertEqual(action.search_view_id, search)
            self.assertEqual(action.view_id, tree)
            self.assertIn(tree, action.view_ids.mapped("view_id"))
        for arch in (
            deduction_search.arch_db,
            deduction_tree.arch_db,
            deduction_cash_tree.arch_db,
            repayment_search.arch_db,
            repayment_tree.arch_db,
        ):
            for token in (
                "business_axis",
                "handling_kind",
                "financial_flow",
                "payment_anchor_policy",
                "direction",
                "legacy_visible_attachment",
            ):
                self.assertNotIn(token, arch)

    def test_expense_deposit_application_actions_use_business_search_filters(self):
        expected_contexts = {
            "smart_construction_core.action_sc_expense_claim_reimbursement_request": "search_default_expense_reimbursement",
            "smart_construction_core.action_sc_expense_claim_project": "search_default_expense_project",
            "smart_construction_core.action_sc_bid_deposit_pay": "search_default_deposit_bid_pay",
            "smart_construction_core.action_sc_bid_deposit_return": "search_default_deposit_bid_return",
            "smart_construction_core.action_sc_contract_deposit_pay": "search_default_deposit_contract_pay",
            "smart_construction_core.action_sc_contract_deposit_return": "search_default_deposit_contract_return",
        }
        search = self.env.ref("smart_construction_core.view_sc_expense_claim_application_search")

        for action_xmlid, search_key in expected_contexts.items():
            action = self.env.ref(action_xmlid)
            context = action.context
            self.assertEqual(action.search_view_id, search)
            self.assertIn("'%s': 1" % search_key, context)
            self.assertNotIn("'search_default_finance_cash_in': 1", context)
            self.assertNotIn("'search_default_finance_cash_out': 1", context)

    def test_expense_deposit_application_actions_use_business_list_view(self):
        action_xmlids = (
            "smart_construction_core.action_sc_expense_claim_reimbursement_request",
            "smart_construction_core.action_sc_expense_claim_project",
            "smart_construction_core.action_sc_bid_deposit_pay",
            "smart_construction_core.action_sc_bid_deposit_return",
            "smart_construction_core.action_sc_contract_deposit_pay",
            "smart_construction_core.action_sc_contract_deposit_return",
        )
        tree = self.env.ref("smart_construction_core.view_sc_expense_claim_application_tree")
        tree_arch = tree.arch_db

        for action_xmlid in action_xmlids:
            action = self.env.ref(action_xmlid)
            self.assertEqual(action.view_id, tree)
            self.assertIn(tree, action.view_ids.mapped("view_id"))
        for token in (
            "business_category_id",
            "project_id",
            "partner_id",
            "expense_type",
            "summary",
            "amount",
            "payment_state",
        ):
            self.assertIn(token, tree_arch)
        for token in (
            "business_axis",
            "handling_kind",
            "financial_flow",
            "payment_anchor_policy",
            "direction",
            "legacy_visible_attachment",
        ):
            self.assertNotIn(token, tree_arch)

    def test_expense_deposit_application_search_is_business_oriented(self):
        search = self.env.ref("smart_construction_core.view_sc_expense_claim_application_search").arch_db
        main_action = self.env.ref("smart_construction_core.action_sc_expense_claim")

        for token in (
            "expense_reimbursement",
            "expense_project",
            "deposit_bid_pay",
            "deposit_bid_return",
            "deposit_contract_pay",
            "deposit_contract_return",
            "group_business_category",
            "group_project",
            "group_partner",
        ):
            self.assertIn(token, search)
        for token in (
            "finance_noncash",
            "finance_interfund",
            "business_axis",
            "handling_kind",
            "financial_flow",
            "payment_anchor_policy",
        ):
            self.assertNotIn(token, search)
        for code in (
            "finance.expense.reimbursement",
            "finance.expense.project",
            "finance.deposit.bid.pay",
            "finance.deposit.bid.return",
            "finance.deposit.contract.pay",
            "finance.deposit.contract.return",
        ):
            self.assertIn(code, main_action.domain)
        self.assertNotIn("deposit_self_funding_return", search)
        self.assertNotIn("finance.deposit.self_funding.return", main_action.domain)

    def test_expense_deposit_application_contract_scopes_business_category_relation(self):
        action = self.env.ref("smart_construction_core.action_sc_expense_claim")
        result = UiContractHandler(self.env).handle(
            {
                "op": "action_open",
                "action_id": action.id,
                "source_mode": "backend_internal",
                "contract_surface": "user",
            },
            {},
        )
        if hasattr(result, "to_legacy_dict"):
            result = result.to_legacy_dict()
        data = result.get("data") or {}
        allowed_codes = data.get("context", {}).get("allowed_business_category_codes") or []
        expected_codes = [
            "finance.expense.reimbursement",
            "finance.expense.project",
            "finance.deposit.bid.pay",
            "finance.deposit.bid.return",
            "finance.deposit.contract.pay",
            "finance.deposit.contract.return",
        ]
        self.assertEqual(allowed_codes, expected_codes)
        relation_domain = (
            data.get("fields", {})
            .get("business_category_id", {})
            .get("relation_entry", {})
            .get("domain", [])
        )
        self.assertIn(["code", "in", expected_codes], relation_domain)
        self.assertIn(["target_model", "=", "sc.expense.claim"], relation_domain)
        self.assertNotIn("finance.deposit.self_funding.return", str(relation_domain))
        search_dialog = (
            data.get("fields", {})
            .get("business_category_id", {})
            .get("relation_entry", {})
            .get("search_dialog", {})
        )
        self.assertEqual(
            [column.get("name") for column in search_dialog.get("columns", [])],
            ["name"],
        )
        self.assertNotIn("domain", search_dialog.get("read_fields", []))
        self.assertNotIn("target_model", search_dialog.get("read_fields", []))
        self.assertNotIn("action_xmlid", search_dialog.get("read_fields", []))

    def test_expense_deposit_legacy_cash_actions_do_not_reuse_generic_search(self):
        application_search = self.env.ref("smart_construction_core.view_sc_expense_claim_application_search")
        application_tree = self.env.ref("smart_construction_core.view_sc_expense_claim_application_tree")
        deposit_search = self.env.ref("smart_construction_core.view_sc_expense_claim_deposit_cash_search")
        tender_search = self.env.ref("smart_construction_core.view_tender_guarantee_search")

        expense_action = self.env.ref("smart_construction_core.action_sc_expense_claim_expense")
        self.assertEqual(expense_action.search_view_id, application_search)
        self.assertEqual(expense_action.view_id, application_tree)
        self.assertIn("finance.expense.reimbursement", expense_action.domain)
        self.assertIn("finance.expense.project", expense_action.domain)
        self.assertIn("'search_default_expense_business': 1", expense_action.context)

        deposit_actions = {
            "smart_construction_core.action_sc_expense_claim_deposit_pay": "search_default_deposit_payment",
            "smart_construction_core.action_sc_expense_claim_deposit_refund": "search_default_deposit_refund",
            "smart_construction_core.action_sc_expense_claim_deposit_receive": "search_default_deposit_receive",
            "smart_construction_core.action_sc_payment_deposit_refund": "search_default_deposit_refund",
        }
        for action_xmlid, search_key in deposit_actions.items():
            action = self.env.ref(action_xmlid)
            self.assertEqual(action.search_view_id, deposit_search)
            self.assertIn("'%s': 1" % search_key, action.context)
            for old_key in (
                "search_default_finance_cash_in",
                "search_default_finance_cash_out",
                "search_default_finance_noncash",
                "search_default_finance_interfund",
            ):
                self.assertNotIn("'%s': 1" % old_key, action.context)

        tender_action = self.env.ref("smart_construction_core.action_sc_payment_deposit_return")
        self.assertEqual(tender_action.res_model, "tender.guarantee")
        self.assertEqual(tender_action.search_view_id, tender_search)

        for arch in (deposit_search.arch_db, tender_search.arch_db):
            for token in (
                "business_axis",
                "handling_kind",
                "financial_flow",
                "payment_anchor_policy",
            ):
                self.assertNotIn(token, arch)
        self.assertNotIn("deposit_self_funding_return", deposit_search.arch_db)
        self.assertIn(
            "('business_category_id.code', '!=', 'finance.deposit.self_funding.return')",
            self.env.ref("smart_construction_core.action_sc_expense_claim_deposit_refund").domain,
        )
        for menu_xmlid in (
            "smart_construction_core.menu_sc_self_funding_deposit",
            "smart_construction_core.menu_sc_self_funding_deposit_refund",
        ):
            self.assertFalse(self.env.ref(menu_xmlid).active)

    def test_self_funding_deposit_refund_is_not_bid_deposit_return(self):
        category = self.env.ref("smart_construction_core.business_category_finance_deposit_self_funding_return")
        bid_return = self.env.ref("smart_construction_core.business_category_finance_deposit_bid_return")
        action = self.env.ref("smart_construction_core.action_sc_self_funding_deposit_refund")

        self.assertEqual(category.code, "finance.deposit.self_funding.return")
        self.assertEqual(category.target_model, "sc.expense.claim")
        self.assertIn("finance.deposit.self_funding.return", action.domain)
        self.assertIn("'default_business_category_code': 'finance.deposit.self_funding.return'", action.context)

        resolved_code = self.env["sc.expense.claim"]._resolve_business_category_code(
            {
                "claim_type": "deposit_refund",
                "guarantee_type": "bid",
                "expense_type": "自筹保证金退回",
            }
        )
        self.assertEqual(resolved_code, "finance.deposit.self_funding.return")

        self_funding_records = self.env["sc.expense.claim"].search(
            [
                ("claim_type", "=", "deposit_refund"),
                "|",
                ("expense_type", "=", "自筹保证金退回"),
                ("legacy_source_table", "=", "C_JFHKLR_TH_ZCDF_CB"),
            ],
            limit=20,
        )
        self.assertTrue(self_funding_records)
        self.assertFalse(self_funding_records.filtered(lambda rec: rec.business_category_id == bid_return))
        self.assertTrue(all(rec.business_category_id == category for rec in self_funding_records))
        self.assertTrue(all(rec.handling_kind == "self_funding_deposit_return" for rec in self_funding_records))

    def test_self_funding_refund_menu_opens_formal_self_funding_refunds(self):
        menu = self.env.ref("smart_construction_core.menu_sc_self_funding_advance_refund")
        action = self.env.ref("smart_construction_core.action_sc_self_funding_registration_refund")

        self.assertEqual(menu.action, action)
        self.assertEqual(action.res_model, "sc.self.funding.registration")
        self.assertIn("finance.self_funding.refund", action.domain)
        self.assertTrue(
            self.env["sc.self.funding.registration"].search_count(
                [("business_category_id.code", "=", "finance.self_funding.refund")]
            )
        )

    def test_formal_user_menu_search_and_list_views_hide_internal_fact_tokens(self):
        bad_search_tokens = (
            "business_axis",
            "handling_kind",
            "financial_flow",
            "payment_anchor_policy",
        )
        bad_tree_tokens = bad_search_tokens + (
            "direction",
            "legacy_visible_attachment",
            "legacy_fact_type",
            "legacy_fact_model",
            "legacy_source",
        )
        roots = (
            "智慧施工管理平台/财务中心",
            "智慧施工管理平台/合同中心",
            "智慧施工管理平台/物资与分包",
            "智慧施工管理平台/施工管理",
            "智慧施工管理平台/人事行政",
            "智慧施工管理平台/用户验收/直营项目系统菜单",
        )
        failures = []

        for menu in self.env["ir.ui.menu"].search([]):
            complete_name = menu.complete_name or ""
            if not any(complete_name.startswith(root) for root in roots):
                continue
            action = menu.action
            if not action or action._name != "ir.actions.act_window":
                continue
            search_arch = action.search_view_id.arch_db if action.search_view_id else ""
            tree = action.view_id if action.view_id and action.view_id.type == "tree" else False
            if not tree:
                for action_view in action.view_ids:
                    if action_view.view_mode == "tree" and action_view.view_id:
                        tree = action_view.view_id
                        break
            tree_arch = tree.arch_db if tree else ""
            bad_search = [token for token in bad_search_tokens if token in search_arch]
            bad_tree = [token for token in bad_tree_tokens if token in tree_arch]
            if bad_search or bad_tree:
                failures.append(
                    "%s search=%s tree=%s" % (
                        complete_name,
                        ",".join(bad_search) or "-",
                        ",".join(bad_tree) or "-",
                    )
                )

        self.assertFalse(failures, "\n".join(failures))

    def test_deduction_registration_action_creates_deduction_bill_lines(self):
        action = self.env.ref("smart_construction_core.action_sc_expense_claim_deduction_bill")
        category = self.env.ref("smart_construction_core.business_category_finance_deduction_bill")
        tree = self.env.ref("smart_construction_core.view_sc_expense_claim_deduction_registration_tree")
        form = self.env.ref("smart_construction_core.view_sc_expense_claim_deduction_registration_form")
        noncash_group = self.env.ref("smart_construction_core.menu_sc_noncash_business_group")
        cash_group = self.env.ref("smart_construction_core.menu_sc_expense_reimbursement_group")
        deduction_menu = self.env.ref("smart_construction_core.menu_sc_deduction_bill")
        deduction_paid_menu = self.env.ref("smart_construction_core.menu_sc_deduction_paid")
        legacy_claim = self.env["sc.expense.claim"].create(
            {
                "claim_type": "expense",
                "expense_type": "扣款单",
                "summary": "扣款单",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
                "deduction_line_ids": [
                    (
                        0,
                        0,
                        {
                            "item_name": "代扣税费",
                            "deduction_category": "enterprise_income_tax",
                            "amount": 100,
                        },
                    )
                ],
            }
        )
        new_claim = self.env["sc.expense.claim"].create(
            {
                "claim_type": "expense",
                "expense_type": "扣款登记",
                "summary": "代扣税费后列支",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
                "deduction_line_ids": [
                    (
                        0,
                        0,
                        {
                            "item_name": "代扣税费",
                            "deduction_category": "enterprise_income_tax",
                            "amount": 100,
                        },
                    )
                ],
                "attachment_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "deduction-registration.txt",
                            "datas": "ZGVkdWN0aW9u",
                        },
                    )
                ],
            }
        )
        auto_amount_claim = self.env["sc.expense.claim"].with_context(
            default_business_category_code="finance.deduction.bill",
        ).create(
            {
                "claim_type": "expense",
                "expense_type": "扣款登记",
                "summary": "只填明细自动汇总金额",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "deduction_line_ids": [
                    (
                        0,
                        0,
                        {
                            "item_name": "管理费",
                            "deduction_category": "management_fee",
                            "amount": 60,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "item_name": "税费",
                            "deduction_category": "vat",
                            "amount": 40,
                        },
                    ),
                ],
            }
        )
        amount_sync_claim = self.env["sc.expense.claim"].with_context(
            default_business_category_code="finance.deduction.bill",
        ).create(
            {
                "claim_type": "expense",
                "expense_type": "扣款登记",
                "summary": "编辑明细后自动同步金额",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "deduction_line_ids": [
                    (
                        0,
                        0,
                        {
                            "item_name": "管理费",
                            "deduction_category": "management_fee",
                            "amount": 60,
                        },
                    )
                ],
            }
        )
        missing_line_claim = self.env["sc.expense.claim"].create(
            {
                "claim_type": "expense",
                "expense_type": "扣款登记",
                "summary": "只有表头金额的扣款登记",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
            }
        )
        mismatch_claim = self.env["sc.expense.claim"].create(
            {
                "claim_type": "expense",
                "expense_type": "扣款登记",
                "summary": "明细合计不一致",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "amount": 100,
                "deduction_line_ids": [
                    (
                        0,
                        0,
                        {
                            "item_name": "代扣税费",
                            "deduction_category": "enterprise_income_tax",
                            "amount": 80,
                        },
                    )
                ],
            }
        )

        self.assertEqual(action.name, "扣款登记")
        self.assertIn("'default_expense_type': '扣款登记'", action.context)
        self.assertEqual(action.view_id, tree)
        self.assertEqual(deduction_menu.parent_id, noncash_group)
        self.assertEqual(deduction_paid_menu.parent_id, cash_group)
        self.assertIn('string="扣款登记"', tree.arch_db)
        self.assertIn('string="扣款单类型"', tree.arch_db)
        self.assertIn('string="扣款事项"', tree.arch_db)
        self.assertNotIn('name="guarantee_type"', tree.arch_db)
        self.assertNotIn('name="payment_account_name"', tree.arch_db)
        self.assertIn('string="扣款登记"', form.arch_db)
        self.assertIn('string="扣款单明细"', form.arch_db)
        self.assertIn('name="deduction_line_ids"', form.arch_db)
        self.assertIn('name="deduction_line_amount_total"', form.arch_db)
        self.assertIn('string="金额由扣款单明细汇总"', form.arch_db)
        self.assertIn('name="amount" string="本次扣款金额" readonly="1"', form.arch_db)
        self.assertLess(form.arch_db.index('name="deduction_line_ids"'), form.arch_db.index('string="金额由扣款单明细汇总"'))
        self.assertIn('string="责任方"', form.arch_db)
        self.assertIn('string="登记日期"', form.arch_db)
        self.assertNotIn('string="扣款单类型"', form.arch_db)
        self.assertNotIn('string="业务域"', form.arch_db)
        self.assertNotIn('string="财务影响"', form.arch_db)
        self.assertNotIn('string="申请锚点口径"', form.arch_db)
        self.assertNotIn('name="guarantee_type"', form.arch_db)
        self.assertNotIn('name="payment_account_name"', form.arch_db)
        self.assertIn(form, action.view_ids.mapped("view_id"))
        self.assertEqual(category.name, "扣款登记")
        self.assertEqual(legacy_claim.handling_kind, "deduction_bill")
        self.assertEqual(new_claim.handling_kind, "deduction_bill")
        self.assertEqual(new_claim.business_axis, "deduction")
        self.assertEqual(new_claim.financial_flow, "noncash")
        self.assertEqual(new_claim.payment_anchor_policy, "noncash_no_request")
        self.assertEqual(new_claim.deduction_line_amount_total, 100)
        self.assertEqual(auto_amount_claim.amount, 100)
        self.assertEqual(auto_amount_claim.approved_amount, 100)
        self.assertEqual(auto_amount_claim.deduction_line_amount_total, 100)
        amount_sync_line = amount_sync_claim.deduction_line_ids[0]
        amount_sync_claim.write({"deduction_line_ids": [(1, amount_sync_line.id, {"amount": 80})]})
        self.assertEqual(amount_sync_claim.amount, 80)
        self.assertEqual(amount_sync_claim.approved_amount, 80)
        self.assertEqual(amount_sync_claim.deduction_line_amount_total, 80)
        amount_sync_claim.write({"deduction_line_ids": [(2, amount_sync_line.id)]})
        self.assertEqual(amount_sync_claim.amount, 0)
        self.assertEqual(amount_sync_claim.approved_amount, 0)
        self.assertEqual(amount_sync_claim.deduction_line_amount_total, 0)
        line_field = self.env["sc.expense.claim.deduction.line"]._fields["deduction_category"]
        line_labels = dict(line_field.selection)
        for category in ("management_fee", "enterprise_income_tax", "vat", "vat_surcharge", "construction_stamp_tax", "purchase_sale_stamp_tax", "vat_nonrefundable"):
            self.assertIn(category, line_labels)
        new_claim._check_business_ready()
        with self.assertRaisesRegex(UserError, "至少一条扣款单明细"):
            missing_line_claim._check_business_ready()
        with self.assertRaisesRegex(UserError, "明细金额合计必须等于本次扣款金额"):
            mismatch_claim._check_business_ready()

    def test_deduction_registration_is_released_in_noncash_frontend_menu(self):
        self.env["sc.product.policy"].sync_construction_menu_product_policies()
        for product_key in ("construction.standard", "construction.preview"):
            policy = self.env["sc.product.policy"].search([("product_key", "=", product_key)], limit=1)
            menus = [
                menu
                for group in (policy.menu_groups or [])
                if isinstance(group, dict)
                for menu in (group.get("menus") or [])
                if isinstance(menu, dict)
            ]
            deduction_menu = next(
                menu
                for menu in menus
                if (
                    menu.get("menu_xmlid")
                    or menu.get("page_key")
                    or menu.get("menu_key")
                ) == "smart_construction_core.menu_sc_deduction_bill"
            )
            paid_menu = next(
                menu
                for menu in menus
                if (
                    menu.get("menu_xmlid")
                    or menu.get("page_key")
                    or menu.get("menu_key")
                ) == "smart_construction_core.menu_sc_deduction_paid"
            )

            self.assertEqual(deduction_menu.get("label"), "扣款登记")
            self.assertIn("非现金业务管理", deduction_menu.get("visible_menu_path"))
            self.assertEqual(deduction_menu.get("product_domain"), "finance_noncash")
            self.assertEqual(deduction_menu.get("default_business_category_code"), "finance.deduction.bill")
            self.assertEqual(deduction_menu.get("route"), "/a/%s?menu_id=%s" % (deduction_menu.get("action_id"), deduction_menu.get("menu_id")))
            self.assertIn("费用/保证金现金办理", paid_menu.get("visible_menu_path"))
            self.assertEqual(paid_menu.get("product_domain"), "finance_cash")

    def test_self_funding_refund_product_entry_uses_formal_self_funding_refund(self):
        self.env["sc.product.policy"].sync_construction_menu_product_policies()
        for product_key in ("construction.standard", "construction.preview"):
            policy = self.env["sc.product.policy"].search([("product_key", "=", product_key)], limit=1)
            menus = [
                menu
                for group in (policy.menu_groups or [])
                if isinstance(group, dict)
                for menu in (group.get("menus") or [])
                if isinstance(menu, dict)
            ]
            refund_menu = next(
                menu
                for menu in menus
                if (
                    menu.get("menu_xmlid")
                    or menu.get("page_key")
                    or menu.get("menu_key")
                ) == "smart_construction_core.menu_sc_self_funding_advance_refund"
            )

            self.assertEqual(refund_menu.get("action_id"), self.env.ref("smart_construction_core.action_sc_self_funding_registration_refund").id)
            self.assertEqual(refund_menu.get("label"), "自筹退回办理")
            self.assertEqual(refund_menu.get("product_domain"), "finance")
            self.assertEqual(refund_menu.get("visible_menu_path"), "智慧施工管理平台 / 财务中心 / 自筹退回办理")
            self.assertEqual(refund_menu.get("default_business_category_code"), "finance.self_funding.refund")
            self.assertEqual(refund_menu.get("allowed_business_category_codes"), ["finance.self_funding.refund"])
            self.assertEqual(refund_menu.get("integration_target"), "sc.self.funding.registration 自筹退回办理")
            self.assertEqual(refund_menu.get("integration_model"), "sc.self.funding.registration")
            self.assertEqual(refund_menu.get("integration_action_xmlid"), "smart_construction_core.action_sc_self_funding_registration_refund")
            self.assertNotEqual(refund_menu.get("integration_model"), "sc.expense.claim")
            for menu in menus:
                self.assertNotIn(
                    menu.get("menu_xmlid") or menu.get("page_key") or menu.get("menu_key"),
                    {
                        "smart_construction_core.menu_sc_self_funding_deposit",
                        "smart_construction_core.menu_sc_self_funding_deposit_refund",
                        "smart_construction_core.menu_scbs55_user_acceptance_180_自筹保证金",
                        "smart_construction_core.menu_scbs55_user_acceptance_190_自筹保证金退回",
                    },
                )
                if menu.get("integration_target") == "sc.expense.claim 费用/保证金申请":
                    self.assertNotIn(
                        "finance.deposit.self_funding.return",
                        menu.get("allowed_business_category_codes") or [],
                    )

    def test_repayment_registration_is_interfund_business_entry(self):
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

        self.assertEqual(claim.business_axis, "interfund")
        self.assertEqual(claim.handling_kind, "repayment_registration")
        self.assertEqual(claim.financial_flow, "interfund")
        self.assertIn("finance.repayment.registration", action.domain)
        self.assertIn("'search_default_repayment_registration': 1", action.context)
        self.assertNotIn("'search_default_finance_interfund': 1", action.context)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_expense_claim_tree").active)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_financing_loan_tree").active)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_receipt_income_tree").active)
        self.assertFalse(self.env.ref("smart_construction_core.view_audit_fields_view_sc_payment_execution_tree").active)
