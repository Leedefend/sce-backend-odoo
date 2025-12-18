# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestConstructionContract(TransactionCase):
    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({"name": "合同中心测试项目"})
        self.partner = self.env["res.partner"].create({"name": "测试客户"})
        self.uom_unit = self.env.ref("uom.product_uom_unit")
        self.wbs = self.env["construction.work.breakdown"].create({
            "name": "结构工程",
            "code": "WBS-TEST",
            "project_id": self.project.id,
        })
        self.tax_sale_9 = self.env.ref("smart_construction_core.tax_sale_vat_9")
        self.budget = self.env["project.budget"].create({
            "name": "控制版",
            "project_id": self.project.id,
        })
        self.boq_line_1 = self.env["project.budget.boq.line"].create({
            "budget_id": self.budget.id,
            "name": "主体结构",
            "wbs_id": self.wbs.id,
            "uom_id": self.uom_unit.id,
            "qty_bidded": 10,
            "price_bidded": 1000.0,
        })
        self.boq_line_2 = self.env["project.budget.boq.line"].create({
            "budget_id": self.budget.id,
            "name": "装修工程",
            "wbs_id": self.wbs.id,
            "uom_id": self.uom_unit.id,
            "qty_bidded": 5,
            "price_bidded": 500.0,
        })

    def test_contract_state_and_amount(self):
        contract = self.env["construction.contract"].create(
            {
                "type": "out",
                "subject": "测试合同",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "tax_id": self.tax_sale_9.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_1.id,
                            "qty_contract": 10,
                            "price_contract": 1000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "boq_line_id": self.boq_line_2.id,
                            "qty_contract": 5,
                            "price_contract": 500.0,
                        },
                    ),
                ],
            }
        )
        self.assertNotEqual(contract.name, "新建")
        self.assertEqual(contract.line_amount_total, 12500.0)
        self.assertEqual(contract.amount_untaxed, 12500.0)
        self.assertAlmostEqual(contract.amount_tax, 1125.0)
        self.assertAlmostEqual(contract.amount_total, 13625.0)
        contract.action_confirm()
        self.assertEqual(contract.state, "confirmed")
        contract.action_set_running()
        self.assertEqual(contract.state, "running")
        contract.action_close()
        self.assertEqual(contract.state, "closed")

    def test_generate_lines_from_budget(self):
        contract = self.env["construction.contract"].create(
            {
                "type": "out",
                "subject": "生成清单合同",
                "project_id": self.project.id,
                "partner_id": self.partner.id,
                "budget_id": self.budget.id,
            }
        )
        contract.action_generate_lines_from_budget()
        self.assertEqual(len(contract.line_ids), 2)
        first_line = contract.line_ids.sorted(key=lambda l: l.sequence)[0]
        self.assertEqual(first_line.boq_line_id, self.boq_line_1)
        self.assertEqual(first_line.qty_contract, 10)
        self.assertEqual(first_line.price_contract, 1000.0)
