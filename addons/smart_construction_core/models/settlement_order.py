# -*- coding: utf-8 -*-
from odoo import _, api, fields, models


class ScSettlementOrder(models.Model):
    _name = "sc.settlement.order"
    _description = "Settlement Order"
    _order = "id desc"

    name = fields.Char(string="结算单号", required=True, default="New", copy=False)
    type = fields.Selection(
        [("cost", "支出结算"), ("income", "收入结算")],
        string="类型",
        default="cost",
    )
    project_id = fields.Many2one(
        "project.project",
        string="项目",
        index=True,
    )
    contract_id = fields.Many2one(
        "project.contract",
        string="合同",
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位")
    date_settlement = fields.Date(string="结算日期")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    amount_untaxed = fields.Monetary(string="不含税金额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_tax = fields.Monetary(string="税额", currency_field="currency_id", compute="_compute_amounts", store=True)
    amount_total = fields.Monetary(string="金额合计", currency_field="currency_id", compute="_compute_amounts", store=True)

    line_ids = fields.One2many(
        "sc.settlement.order.line",
        "order_id",
        string="结算行",
    )

    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("submit", "提交"),
            ("approved", "批准"),
            ("done", "完成"),
            ("cancel", "取消"),
        ],
        string="状态",
        default="draft",
        tracking=True,
    )

    @api.depends("line_ids.amount_total")
    def _compute_amounts(self):
        for order in self:
            untaxed = 0.0
            tax = 0.0
            for line in order.line_ids:
                untaxed += line.amount_total
            order.amount_untaxed = untaxed
            order.amount_tax = tax
            order.amount_total = untaxed + tax

    @api.model
    def create(self, vals):
        if vals.get("name", "New") in (False, "New"):
            seq = self.env["ir.sequence"].next_by_code("sc.settlement.order")
            vals["name"] = seq or _("Settlement")
        return super().create(vals)

    def action_submit(self):
        self.write({"state": "submit"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancel"})


class ScSettlementOrderLine(models.Model):
    _name = "sc.settlement.order.line"
    _description = "Settlement Order Line"
    _order = "id"

    order_id = fields.Many2one(
        "sc.settlement.order",
        string="结算单",
        required=True,
        ondelete="cascade",
    )
    purchase_line_id = fields.Many2one("purchase.order.line", string="采购行")
    product_id = fields.Many2one("product.product", string="产品")
    cost_item_id = fields.Many2one(
        "sc.dictionary",
        string="成本项",
        domain=[("type", "=", "cost_item")],
    )
    uom_id = fields.Many2one("uom.uom", string="单位")
    qty_source = fields.Float(string="源单数量", digits="Product Unit of Measure")
    qty_settle = fields.Float(string="结算数量", digits="Product Unit of Measure")
    price_unit = fields.Float(string="结算单价", digits="Product Price")
    amount_total = fields.Monetary(string="金额", currency_field="currency_id", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        related="order_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("qty_settle", "price_unit")
    def _compute_amount(self):
        for line in self:
            qty = line.qty_settle or 0.0
            price = line.price_unit or 0.0
            line.amount_total = qty * price
