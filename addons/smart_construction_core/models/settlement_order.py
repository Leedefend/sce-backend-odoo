# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ScSettlementOrder(models.Model):
    _name = "sc.settlement.order"
    _description = "Settlement Order"
    _order = "id desc"

    name = fields.Char(string="结算单号", required=True, default="新建", copy=False)
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
    )
    contract_id = fields.Many2one(
        "construction.contract",
        string="合同",
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", required=True)
    settlement_type = fields.Selection(
        [("out", "支出结算"), ("in", "收入结算")],
        string="结算类型",
        default="out",
    )
    date_settlement = fields.Date(string="结算日期", default=fields.Date.context_today)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    amount_total = fields.Monetary(
        string="金额合计",
        currency_field="currency_id",
        compute="_compute_amount_total",
        store=True,
    )
    note = fields.Text(string="备注")

    line_ids = fields.One2many(
        "sc.settlement.order.line",
        "settlement_id",
        string="结算行",
    )
    payment_request_ids = fields.One2many(
        "payment.request",
        "settlement_id",
        string="付款申请",
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string="已付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amount",
        store=True,
    )
    remaining_amount = fields.Monetary(
        string="待付款金额",
        currency_field="currency_id",
        compute="_compute_paid_amount",
        store=True,
    )

    @api.depends("line_ids.amount", "payment_request_ids", "payment_request_ids.state")
    def _compute_paid_amount(self):
        Ledger = self.env["sc.treasury.ledger"].sudo()
        for order in self:
            total = order.amount_total or 0.0
            paid = 0.0
            if order.id:
                paid = sum(
                    Ledger.search(
                        [("settlement_id", "=", order.id), ("state", "=", "posted")]
                    ).mapped("amount")
                )
            order.paid_amount = paid
            order.remaining_amount = total - paid

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "提交"),
            ("approve", "批准"),
            ("done", "完成"),
            ("cancel", "取消"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )

    @api.depends("line_ids.amount")
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped("amount"))

    @api.model
    def create(self, vals):
        if vals.get("name", "新建") in (False, "新建"):
            seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
            vals["name"] = seq or _("Settlement")
        return super().create(vals)

    def action_submit(self):
        self.write({"state": "submit"})

    def action_approve(self):
        self.write({"state": "approve"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})


class ScSettlementOrderLine(models.Model):
    _name = "sc.settlement.order.line"
    _description = "Settlement Order Line"
    _order = "id"

    settlement_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="名称", required=True)
    qty = fields.Float(string="数量", default=1.0, digits="Product Unit of Measure")
    price_unit = fields.Monetary(string="单价", currency_field="currency_id", default=0.0, digits="Product Price")
    amount = fields.Monetary(string="金额", currency_field="currency_id", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="settlement_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("qty", "price_unit")
    def _compute_amount(self):
        for line in self:
            line.amount = (line.qty or 0.0) * (line.price_unit or 0.0)
