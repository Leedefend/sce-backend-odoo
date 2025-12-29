# -*- coding: utf-8 -*-
from odoo import models


class ProjectProjectFinancial(models.Model):
    _inherit = "project.project"

    def action_open_project_budgets(self):
        """从项目详情页打开当前项目的预算列表。"""
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_project_budget").read()[0]

        action["domain"] = [("project_id", "=", self.id)]
        ctx = dict(self.env.context)
        ctx.update({"default_project_id": self.id})
        action["context"] = ctx
        return action

    def action_open_project_contracts(self):
        """从项目详情页打开当前项目的合同列表。"""
        self.ensure_one()
        action = self.env.ref("smart_construction_core.action_construction_contract").read()[0]

        action["domain"] = [("project_id", "=", self.id)]
        ctx = dict(self.env.context)
        ctx.update({"default_project_id": self.id})
        action["context"] = ctx
        return action
