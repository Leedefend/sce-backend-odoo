# -*- coding: utf-8 -*-
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
            }
        )

        self.assertEqual(supplier.sc_supplier_type, "material")
        self.assertEqual(supplier.sc_bank_account, "100200300")

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

    def test_legacy_purchase_contract_is_not_business_approval_target(self):
        policy = self.env["sc.approval.policy"].get_active_policy("sc.legacy.purchase.contract.fact")
        self.assertFalse(policy)

        models = self.env["tier.definition"]._get_tier_validation_model_names()
        self.assertNotIn("sc.legacy.purchase.contract.fact", models)

    def test_general_contract_company_view_exposes_contact_columns(self):
        view = self.env.ref("smart_construction_core.view_sc_general_contract_tree")
        arch = view.arch_db

        self.assertIn('tree string="一般合同（公司）"', arch)
        self.assertIn('name="contact_name"', arch)
        self.assertIn('name="contact_phone"', arch)

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
