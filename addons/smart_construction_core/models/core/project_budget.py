# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectBudget(models.Model):
    _name = "project.budget"
    _inherit = ["project.budget", "mail.thread", "mail.activity.mixin"]
    # 兼容旧视图/列表的 active 字段，代理到 is_active，避免缺少数据库列报错
    active = fields.Boolean(related="is_active", string="启用", readonly=False, store=False)


class ProjectBudgetLine(models.Model):
    _name = "project.budget.line"
    _description = "Project Budget Line"

    budget_id = fields.Many2one(
        "project.budget",
        string="预算",
        required=True,
        ondelete="cascade",
        index=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="budget_id.project_id",
        store=True,
        index=True,
    )

    boq_line_id = fields.Many2one(
        "project.boq.line",
        string="清单行",
        index=True,
    )
    boq_code = fields.Char(
        string="清单编码",
        related="boq_line_id.code",
        store=True,
        readonly=True,
    )
    wbs_id = fields.Many2one(
        "project.wbs",
        string="WBS",
        index=True,
    )

    name = fields.Char(string="预算项名称")
    sequence = fields.Integer(string="序号", default=10)

    budget_qty = fields.Float(string="预算工程量")
    budget_price = fields.Monetary(
        string="预算单价",
        currency_field="currency_id",
    )
    budget_amount = fields.Monetary(
        string="预算合价",
        currency_field="currency_id",
    )
    measure_rule = fields.Selection(
        [
            ("by_qty", "按工程量计价"),
            ("lump_sum", "总价包干"),
            ("by_schedule", "按节点"),
        ],
        string="计价方式",
    )
    revenue_recognition = fields.Selection(
        [
            ("progress", "按进度确认收入"),
            ("milestone", "按里程碑确认收入"),
            ("completion", "竣工一次性确认"),
        ],
        string="收入确认方式",
        default="progress",
    )
    alloc_ids = fields.One2many(
        "project.budget.cost.alloc",
        "budget_boq_line_id",
        string="成本分摊",
        help="记录该清单行如何拆值到不同成本科目（兼容旧版视图）",
    )

    # 兼容旧版：预算说明
    note = fields.Text(string="备注")
    uom_id = fields.Many2one(
        "uom.uom",
        string="单位",
        related="boq_line_id.uom_id",
        store=True,
        readonly=True,
    )
    # 兼容旧字段：投标量/价/合价
    qty_bidded = fields.Float(string="标后工程量")
    price_bidded = fields.Monetary(
        string="标后单价",
        currency_field="currency_id",
    )
    amount_bidded = fields.Monetary(
        string="标后合价",
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="budget_id.currency_id",
        store=True,
        readonly=True,
    )

    # compute 逻辑放到 Phase-1 统一处理
