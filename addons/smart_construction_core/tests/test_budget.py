# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase


class TestProjectBudget(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env["project.project"].create({
            "name": "Test Project",
        })

    def test_budget_unique_version(self):
        budget = self.env["project.budget"].create({
            "name": "Budget V1",
            "project_id": self.project.id,
        })
        self.assertEqual(budget.version, "V001")
        with self.assertRaises(Exception):
            self.env["project.budget"].create({
                "name": "Budget V2",
                "project_id": self.project.id,
                "version": budget.version,
            })

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
        ctx = {"copy_allocations": False}
        new_budget = budget.with_context(ctx).action_copy_version()
        res_id = new_budget["res_id"]
        copied = self.env["project.budget"].browse(res_id)
        self.assertFalse(copied.line_ids.mapped("alloc_ids"))
        self.assertEqual(copied.origin_budget_id, budget)
