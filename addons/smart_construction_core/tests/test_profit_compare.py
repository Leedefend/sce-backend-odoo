# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestProjectProfitCompare(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "Profit Project"})
        self.wbs = self.env["construction.work.breakdown"].create({
            "name": "主体结构",
            "code": "WBS-100",
            "project_id": self.project.id,
        })
        self.cost_code = self.env["project.cost.code"].create({
            "name": "材料费",
            "code": "MAT",
            "type": "material",
        })
        budget = self.env["project.budget"].create({
            "name": "Budget",
            "project_id": self.project.id,
        })
        line = self.env["project.budget.boq.line"].create({
            "budget_id": budget.id,
            "name": "桩基工程",
            "wbs_id": self.wbs.id,
            "qty_bidded": 10,
            "price_bidded": 200,
        })
        self.env["project.budget.cost.alloc"].create({
            "project_id": self.project.id,
            "budget_boq_line_id": line.id,
            "cost_code_id": self.cost_code.id,
            "currency_id": budget.currency_id.id,
            "amount_budget": 1200,
        })
        self.env["project.cost.ledger"].create({
            "project_id": self.project.id,
            "wbs_id": self.wbs.id,
            "cost_code_id": self.cost_code.id,
            "currency_id": budget.currency_id.id,
            "date": "2025-01-05",
            "amount": 800,
        })
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.env.ref("base.res_partner_1").id,
            "invoice_date": "2025-01-10",
            "project_id": self.project.id,
            "line_ids": [
                (0, 0, {
                    "name": "收入行",
                    "account_id": self.env["account.account"].search([("internal_group", "=", "income")], limit=1).id,
                    "price_unit": -1500,
                    "quantity": 1,
                    "project_id": self.project.id,
                    "wbs_id": self.wbs.id,
                }),
                (0, 0, {
                    "name": "应收",
                    "account_id": self.env["account.account"].search([("internal_group", "=", "asset")], limit=1).id,
                    "price_unit": 1500,
                    "quantity": 1,
                }),
            ]
        })
        move.action_post()

    def test_profit_view_records(self):
        records = self.env["project.profit.compare"].search([
            ("project_id", "=", self.project.id),
            ("wbs_id", "=", self.wbs.id),
        ])
        self.assertTrue(records)
        rec = records.filtered(lambda r: r.period == "2025-01")
        self.assertTrue(rec)
        rec = rec[0]
        self.assertAlmostEqual(rec.revenue_actual_amount, 1500)
        self.assertAlmostEqual(rec.cost_actual_amount, 800)
        self.assertEqual(rec.revenue_budget_amount, 2000)
        self.assertEqual(rec.cost_budget_amount, 1200)
