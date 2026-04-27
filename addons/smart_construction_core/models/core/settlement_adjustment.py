# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScSettlementAdjustment(models.Model):
    _name = "sc.settlement.adjustment"
    _description = "结算调整"
    _order = "date_adjustment desc, id desc"

    name = fields.Char(string="调整单号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    adjustment_type = fields.Selection(
        [("deduction", "扣款"), ("addition", "调增")],
        string="调整类型",
        default="deduction",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("cancel", "已取消"),
            ("legacy_confirmed", "历史已确认"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    settlement_id = fields.Many2one("sc.settlement.order", string="结算单", index=True, ondelete="set null")
    contract_id = fields.Many2one("construction.contract", string="合同", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    date_adjustment = fields.Date(string="调整日期", default=fields.Date.context_today, index=True)
    item_name = fields.Char(string="调整事项", index=True)
    account_name = fields.Char(string="扣款账户", index=True)
    amount = fields.Monetary(string="调整金额", currency_field="currency_id", required=True)
    signed_amount = fields.Monetary(
        string="影响金额",
        currency_field="currency_id",
        compute="_compute_signed_amount",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    legacy_line_id = fields.Char(string="历史行ID", index=True, readonly=True)
    legacy_document_no = fields.Char(string="历史单据号", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史单据状态", index=True, readonly=True)
    legacy_fund_confirmation_id = fields.Char(string="历史资金确认ID", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean("有效", default=True, index=True)

    _sql_constraints = [
        ("legacy_line_unique", "unique(legacy_line_id)", "Legacy settlement adjustment line id must be unique."),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Adjustment amount must be non-negative."),
    ]

    @api.depends("adjustment_type", "amount")
    def _compute_signed_amount(self):
        for rec in self:
            amount = rec.amount or 0.0
            rec.signed_amount = -amount if rec.adjustment_type == "deduction" else amount

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.settlement.adjustment") or _("结算调整")
            if vals.get("settlement_id"):
                settlement = self.env["sc.settlement.order"].browse(vals["settlement_id"])
                vals.setdefault("project_id", settlement.project_id.id)
                vals.setdefault("contract_id", settlement.contract_id.id)
                vals.setdefault("partner_id", settlement.partner_id.id)
                vals.setdefault("currency_id", settlement.currency_id.id)
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"settlement_id", "contract_id", "partner_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移调整已确认，只允许补充业务锚点和备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirmed"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移调整不能在新系统取消。"))
            if rec.state == "confirmed":
                rec.state = "cancel"


class ScSettlementOrder(models.Model):
    _inherit = "sc.settlement.order"

    adjustment_ids = fields.One2many("sc.settlement.adjustment", "settlement_id", string="结算调整")
    adjustment_total = fields.Monetary(
        string="调整合计",
        currency_field="currency_id",
        compute="_compute_adjustment_totals",
        store=True,
    )
    amount_after_adjustment = fields.Monetary(
        string="调整后金额",
        currency_field="currency_id",
        compute="_compute_adjustment_totals",
        store=True,
    )

    @api.depends("amount_total", "adjustment_ids.signed_amount", "adjustment_ids.state")
    def _compute_adjustment_totals(self):
        for order in self:
            adjustment_total = sum(
                order.adjustment_ids.filtered(lambda rec: rec.state in ("confirmed", "legacy_confirmed")).mapped(
                    "signed_amount"
                )
            )
            order.adjustment_total = adjustment_total
            order.amount_after_adjustment = (order.amount_total or 0.0) + adjustment_total
