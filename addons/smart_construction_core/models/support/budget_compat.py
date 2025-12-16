# -*- coding: utf-8 -*-
from odoo import models


class ProjectBudgetLineCompat(models.Model):
    """
    兼容层：历史模型 project.budget.line -> 现用 project.budget.boq.line。
    避免数据库残留记录升级时报“KeyError: 'project.budget.line'”。 
    """

    _name = "project.budget.line"
    _description = "项目预算行(兼容层)"
    _inherit = "project.budget.boq.line"
    _table = "project_budget_boq_line"
