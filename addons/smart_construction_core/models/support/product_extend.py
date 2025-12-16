# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    """Expose default cost code so仓库/采购无需重复选择。"""

    _inherit = "product.template"

    default_cost_code_id = fields.Many2one(
        "project.cost.code",
        string="默认成本科目",
        domain="[('active','=',True)]",
        help="采购/入库时如未指定成本科目，将自动使用此科目。",
    )
