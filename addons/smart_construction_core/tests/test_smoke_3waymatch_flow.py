# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install", "smoke", "sc_smoke", "smoke_3waymatch")
class TestSmokeThreeWayMatchFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Flow Vendor"})
        cls.project = cls.env["project.project"].create({"name": "Flow Project"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Flow Product",
                "type": "product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
                "uom_po_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )
        cls.contract = cls.env["construction.contract"].create(
            {
                "subject": "Flow Contract",
                "type": "in",
                "project_id": cls.project.id,
                "partner_id": cls.partner.id,
            }
        )
        cls.purchase_order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner.id,
                "project_id": cls.project.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Flow Item",
                            "product_id": cls.product.id,
                            "product_qty": 1,
                            "product_uom": cls.product.uom_po_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        cls.purchase_order.button_confirm()

    def test_minimum_three_way_match_chain(self):
        settlement = self.env["sc.settlement.order"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "purchase_order_ids": [(6, 0, [self.purchase_order.id])],
                "line_ids": [(0, 0, {"name": "Settlement Line", "qty": 1, "price_unit": 100})],
            }
        )
        settlement.action_submit()
        settlement.action_approve()

        request = self.env["payment.request"].create(
            {
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "contract_id": self.contract.id,
                "settlement_id": settlement.id,
                "amount": 80,
                "type": "pay",
            }
        )

        self.assertIn(settlement.compliance_state, ("ok", "warn"))
        self.assertEqual(request.settlement_id, settlement)
        self.assertGreaterEqual(settlement.remaining_amount, request.amount)
