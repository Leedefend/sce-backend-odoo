# -*- coding: utf-8 -*-
from odoo import models


class ProjectBudgetLineCompat(models.Model):
    """
    历史模型门面：将 project.budget.line 指向现用 project.budget.boq.line。
    避免数据库残留记录升级时报“KeyError: 'project.budget.line'”。
    """

    _name = "project.budget.line"
    _description = "项目预算行历史模型门面"
    _inherit = "project.budget.boq.line"
    _table = "project_budget_boq_line"
