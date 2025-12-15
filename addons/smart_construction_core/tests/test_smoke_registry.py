# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("smoke", "sc_smoke", "smoke_registry")
class TestSmokeRegistry(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.settlement_model = cls.env["sc.settlement.order"]
        cls.payment_model = cls.env["payment.request"]
        cls.purchase_model = cls.env["purchase.order"]

    def test_models_are_available(self):
        self.assertEqual(self.settlement_model._name, "sc.settlement.order")
        self.assertEqual(self.payment_model._name, "payment.request")
        self.assertEqual(self.purchase_model._name, "purchase.order")

    def test_settlement_key_fields_exist(self):
        expected = {
            "purchase_order_ids",
            "invoice_ref",
            "invoice_amount",
            "invoice_date",
            "compliance_contract_ok",
            "compliance_state",
            "compliance_message",
        }
        self.assertTrue(expected.issubset(set(self.settlement_model._fields)))

    def test_payment_request_key_fields_exist(self):
        expected = {"project_id", "partner_id", "settlement_id", "amount", "contract_id"}
        self.assertTrue(expected.issubset(set(self.payment_model._fields)))
