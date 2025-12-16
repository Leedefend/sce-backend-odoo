# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    boq_generated = fields.Boolean("来源: BOQ聚合", default=False, index=True)
    boq_group_key = fields.Char("BOQ分组键", index=True)
    boq_section_type = fields.Selection(
        [
            ("building", "建筑"),
            ("installation", "安装/机电"),
            ("decoration", "装饰"),
            ("landscape", "景观"),
            ("other", "其他"),
        ],
        string="工程类别",
        index=True,
    )
    work_id = fields.Many2one(
        "construction.work.breakdown",
        string="工程结构节点",
        ondelete="set null",
        index=True,
    )
    boq_line_ids = fields.Many2many(
        "project.boq.line",
        "project_task_boq_rel",
        "task_id",
        "boq_id",
        string="关联BOQ行",
        readonly=True,
    )
    boq_uom_id = fields.Many2one("uom.uom", string="工程量单位", readonly=True)

    boq_quantity_total = fields.Float(
        "BOQ工程量",
        compute="_compute_boq_totals",
        store=True,
        readonly=True,
    )
    boq_amount_total = fields.Monetary(
        "BOQ合价汇总",
        currency_field="currency_id",
        compute="_compute_boq_totals",
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="project_id.company_id.currency_id",
        store=True,
        readonly=True,
    )

    def _compute_boq_totals(self):
        for task in self:
            qty = sum(task.boq_line_ids.mapped("quantity"))
            amount = sum(task.boq_line_ids.mapped("amount"))
            task.boq_quantity_total = qty
            task.boq_amount_total = amount
            task.boq_uom_id = task.boq_line_ids[:1].uom_id.id if task.boq_line_ids else False
