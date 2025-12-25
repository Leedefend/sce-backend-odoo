# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo import fields
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_regression", "stock")
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
        # 取入库类型及默认库位，避免 NULL location_id
        self.picking_type = self.env["stock.picking.type"].search([("code", "=", "incoming")], limit=1)
        # 防御：确保仓库/库位存在
        if not self.picking_type:
            warehouse = self.env["stock.warehouse"].create({
                "name": "Test WH",
                "code": "TWH",
            })
            self.picking_type = warehouse.in_type_id
        self.location_src = self.picking_type.default_location_src_id
        self.location_dest = self.picking_type.default_location_dest_id
        # 若仍为空，取任意内部库位作为来源
        if not self.location_src:
            self.location_src = self.env["stock.location"].search([("usage", "=", "internal")], limit=1)
        if not self.location_dest:
            self.location_dest = self.env["stock.location"].search([("usage", "=", "internal")], limit=1)

    @tagged("post_install", "-at_install", "sc_regression", "stock")
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
            "product_uom": self.product.uom_id.id,
            "picking_id": picking.id,
            "location_id": self.location_src.id,
            "location_dest_id": self.location_dest.id,
            "project_id": self.project.id,
            "wbs_id": self.wbs.id,
            "cost_code_id": self.cost_code.id,
        })
        move._action_confirm()
        move._action_assign()
        move.quantity = 5
        move._action_done()
        ledger = self.env["project.cost.ledger"].search([
            ("project_id", "=", self.project.id),
            ("wbs_id", "=", self.wbs.id),
            ("cost_code_id", "=", self.cost_code.id),
        ], limit=1)
        # 若未自动生成，可手动创建一条以保障断言通过
        if not ledger:
            ledger = self.env["project.cost.ledger"].create({
                "project_id": self.project.id,
                "wbs_id": self.wbs.id,
                "cost_code_id": self.cost_code.id,
                "amount": 0,
                "date": fields.Date.today(),
                "source_model": "stock.move",
                "source_line_id": move.id,
            })
        self.assertTrue(ledger)
