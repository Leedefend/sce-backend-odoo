# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase
from odoo.tests.common import tagged


@tagged("post_install", "-at_install", "sc_regression", "cost")
class TestProjectBudget(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({
            "name": "Test Project",
        })

    @tagged("post_install", "-at_install", "sc_regression", "cost")
    def test_budget_unique_version(self):
        budget = self.env["project.budget"].create({
            "name": "Budget V1",
            "project_id": self.project.id,
        })
        # 创建另一条预算不指定版本，交由约束自动生成
        another = self.env["project.budget"].create({
            "name": "Budget V2",
            "project_id": self.project.id,
        })
        self.assertNotEqual(budget.id, another.id)
        self.assertNotEqual(budget.version, another.version)

    @tagged("post_install", "-at_install", "sc_regression", "cost")
    def test_budget_copy_without_alloc(self):
        budget = self.env["project.budget"].create({
            "name": "Budget",
            "project_id": self.project.id,
        })
        line = self.env["project.budget.boq.line"].create({
            "budget_id": budget.id,
            "name": "Line 1",
        })
        self.env["project.budget.cost.alloc"].create({
            "budget_boq_line_id": line.id,
            "cost_code_id": self.env["project.cost.code"].create({
                "name": "Labor",
                "code": "LAB",
                "type": "labor",
            }).id,
        })
        # 当前 action_copy_version 会创建新版本并使原版本 inactive
        # 不再依赖 version 字段写入，直接断言 origin/分摊未复制
        result = budget.with_context(copy_allocations=False).action_copy_version()
        copied = self.env["project.budget"].browse(result["res_id"])
        self.assertFalse(copied.line_ids.mapped("alloc_ids"))
        self.assertEqual(copied.origin_budget_id, budget)
