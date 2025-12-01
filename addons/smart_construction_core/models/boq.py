# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProjectBoqLine(models.Model):
    """工程量清单（平铺）"""

    _name = "project.boq.line"
    _description = "工程量清单"
    _order = "project_id, sequence, id"

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
    )
    sequence = fields.Integer("序号", default=10)
    section_type = fields.Selection(
        [
            ("building", "建筑"),
            ("installation", "安装/机电"),
            ("decoration", "装饰"),
            ("landscape", "景观"),
            ("other", "其他"),
        ],
        string="工程类别",
    )
    code = fields.Char("清单编码")
    name = fields.Char("清单名称", required=True)
    spec = fields.Char("规格/项目特征")
    uom_id = fields.Many2one("uom.uom", string="单位")
    quantity = fields.Float("工程量", default=0.0)
    price = fields.Monetary("单价", currency_field="currency_id")
    amount = fields.Monetary(
        "合价",
        currency_field="currency_id",
        compute="_compute_amount",
        store=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    cost_item_id = fields.Many2one(
        "sc.dictionary",
        string="成本项",
        domain=[("type", "=", "cost_item")],
    )
    task_id = fields.Many2one(
        "project.task",
        string="关联任务",
        ondelete="set null",
        index=True,
    )
    work_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构",
        ondelete="set null",
        index=True,
    )

    remark = fields.Char("备注")
    is_provisional = fields.Boolean("暂列/暂估")
    category = fields.Selection(
        [
            ("subitem", "分部分项"),
            ("measure", "措施项目"),
            ("other", "其他项目"),
        ],
        string="项目类别",
    )

    @api.depends("quantity", "price")
    def _compute_amount(self):
        for rec in self:
            qty = rec.quantity or 0.0
            price = rec.price or 0.0
            rec.amount = qty * price
