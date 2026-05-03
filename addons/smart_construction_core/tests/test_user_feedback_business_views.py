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
        supplier = self.env["res.partner"].create({"name": "Feedback RFQ Supplier", "supplier_rank": 1})
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
                    )
                ],
            }
        )

        self.assertEqual(rfq.contact_name, "张三")
        self.assertEqual(rfq.supplier_ids, supplier)

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
