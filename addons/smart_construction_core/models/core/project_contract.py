# -*- coding: utf-8 -*-
from odoo import fields, models


class ProjectContract(models.Model):
    _name = "project.contract"
    _description = "Project Contract"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "project_id, id"

    name = fields.Char(string="合同名称", required=True, tracking=True)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="cascade",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="合同对方",
        tracking=True,
    )
    contract_type = fields.Selection(
        [
            ("revenue", "收入合同"),
            ("subcontract", "分包合同"),
            ("purchase", "采购合同"),
        ],
        string="合同类型",
        required=True,
        default="revenue",
        tracking=True,
    )
    active = fields.Boolean(string="启用", default=True)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(
        string="合同金额合计",
        currency_field="currency_id",
        help="当前阶段暂不做自动汇总，作为录入占位字段，后续 Phase-1 再加 compute。",
    )

    date_start = fields.Date(string="合同开始日期")
    date_end = fields.Date(string="合同结束日期")
    note = fields.Text(string="备注")

    line_ids = fields.One2many(
        "project.contract.line",
        "contract_id",
        string="合同行",
    )

    _sql_constraints = [
        (
            "project_contract_unique_name",
            "unique(project_id, name, contract_type)",
            "同一项目下，同一类型的合同名称必须唯一。",
        ),
    ]


class ProjectContractLine(models.Model):
    _name = "project.contract.line"
    _description = "Project Contract Line"
    _order = "sequence, id"

    contract_id = fields.Many2one(
        "project.contract",
        string="合同",
        required=True,
        ondelete="cascade",
        index=True,
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        related="contract_id.project_id",
        store=True,
        index=True,
    )

    sequence = fields.Integer(string="序号", default=10)
    name = fields.Char(string="内容 / 清单名称", required=True)

    boq_line_id = fields.Many2one(
        "project.boq.line",
        string="清单行",
        help="关联工程量清单行，用于后续五算对比与台账联动。",
    )

    # ⚠️ 如果你的 WBS 模型名字不是 project.wbs（比如 project.wbs.node），
    # 请把下面 comodel_name 改成实际的模型名再重启服务。
    wbs_id = fields.Many2one(
        "project.wbs",
        string="WBS",
        help="关联 WBS 结构，后续用于 WBS 维度的汇总与分析。",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="contract_id.currency_id",
        store=True,
        readonly=True,
    )

    contract_qty = fields.Float(
        string="合同工程量",
        digits="Product Unit of Measure",
    )
    contract_price = fields.Monetary(
        string="合同单价",
        currency_field="currency_id",
    )
    contract_amount = fields.Monetary(
        string="合同合价",
        currency_field="currency_id",
        help="当前阶段不自动 = qty * price，先作为录入字段，后续再加 compute。",
    )

    note = fields.Char(string="备注")
