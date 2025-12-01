# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestStockCostLedger(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "Project Cost Test"})
        self.wbs = self.env["construction.work.breakdown"].create({
            "name": "Root",
            "code": "WBS-001",
            "project_id": self.project.id,
        })
        self.cost_code = self.env["project.cost.code"].create({
            "name": "材料费",
            "code": "MAT",
            "type": "material",
        })
        self.partner = self.env["res.partner"].create({"name": "Vendor"})
        self.product = self.env["product.product"].create({
            "name": "Test Material",
            "type": "product",
            "default_cost_code_id": self.cost_code.id,
        })
        self.picking_type = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)
        self.location_src = self.picking_type.default_location_src_id
        self.location_dest = self.picking_type.default_location_dest_id

    def test_cost_ledger_created_on_receipt(self):
        picking = self.env["stock.picking"].create({
            "name": "WH/IN/0001",
            "partner_id": self.partner.id,
            "picking_type_id": self.picking_type.id,
            "location_id": self.location_src.id,
            "location_dest_id": self.location_dest.id,
        })
        move = self.env["stock.move"].create({
            "name": self.product.name,
            "product_id": self.product.id,
            "product_uom_qty": 5,
            "quantity_done": 5,
            "product_uom": self.product.uom_id.id,
            "picking_id": picking.id,
            "location_id": self.location_src.id,
            "location_dest_id": self.location_dest.id,
            "project_id": self.project.id,
            "wbs_id": self.wbs.id,
            "cost_code_id": self.cost_code.id,
        })
        move.quantity_done = 5
        picking._create_cost_ledger_from_moves()
        ledger = self.env["project.cost.ledger"].search([
            ("source_model", "=", "stock.move"),
            ("source_line_id", "=", move.id),
        ])
        self.assertTrue(ledger)
        self.assertEqual(ledger.project_id, self.project)
        self.assertEqual(ledger.wbs_id, self.wbs)
        self.assertEqual(ledger.cost_code_id, self.cost_code)
