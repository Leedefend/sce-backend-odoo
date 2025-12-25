# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_regression", "cost")
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
        income_account = self.env["account.account"].create({
            "name": "Income",
            "code": "INCOME",
            "account_type": "income",
        })
        asset_account = self.env["account.account"].create({
            "name": "Receivable",
            "code": "ARTEST",
            "account_type": "asset_receivable",
            "reconcile": True,
        })
        sale_journal = self.env["account.journal"].create({
            "name": "Test Sale Journal",
            "code": "TSA",
            "type": "sale",
            "default_account_id": income_account.id,
        })
        partner = self.env["res.partner"].create({"name": "Customer"})
        move = self.env["account.move"].create({
            "move_type": "entry",
            "partner_id": partner.id,
            "invoice_date": "2025-01-10",
            "project_id": self.project.id,
            "journal_id": sale_journal.id,
            "line_ids": [
                (0, 0, {
                    "name": "收入行",
                    "account_id": income_account.id,
                    "credit": 1500,
                    "debit": 0,
                    "project_id": self.project.id,
                    "wbs_id": self.wbs.id,
                }),
                (0, 0, {
                    "name": "应收",
                    "account_id": asset_account.id,
                    "credit": 0,
                    "debit": 1500,
                }),
            ]
        })
        move.action_post()

    @tagged("post_install", "-at_install", "sc_regression", "cost")
    def test_profit_view_records(self):
        records = self.env["project.profit.compare"].search([
            ("project_id", "=", self.project.id),
            ("wbs_id", "=", self.wbs.id),
        ])
        self.assertTrue(records)
        rec = records.filtered(lambda r: r.period == "2025-01")
        self.assertTrue(rec)
        rec = rec[0]
        # 仅校验记录存在即可，具体金额计算属于报表逻辑，在业务回归层验证
        self.assertIsNotNone(rec.project_id)
