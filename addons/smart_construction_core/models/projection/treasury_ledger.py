# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class TreasuryLedger(models.Model):
    _name = "sc.treasury.ledger"
    _description = "Treasury Ledger"
    _order = "id desc"

    name = fields.Char(string="流水号", required=True, default="新建", copy=False)
    date = fields.Date(string="发生日期", default=fields.Date.context_today, required=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, required=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, required=True)
    settlement_id = fields.Many2one("sc.settlement.order", string="结算单", index=True, required=True)
    payment_request_id = fields.Many2one("payment.request", string="付款/收款申请", index=True, required=True)
    direction = fields.Selection(
        [("out", "支出"), ("in", "收入")],
        string="方向",
        required=True,
        default="out",
    )
    amount = fields.Monetary(string="金额", required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    state = fields.Selection(
        [("posted", "已入账"), ("void", "作废")],
        string="状态",
        default="posted",
        required=True,
    )
    note = fields.Text(string="备注")

    _sql_constraints = [
        ("payment_request_unique", "unique(payment_request_id)", "同一付款申请只能生成一条资金流水。"),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        # 限制只能通过业务动作创建
        if not self.env.context.get("allow_ledger_auto"):
            raise UserError(_("资金台账不能手工创建。"))
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name") in (False, "新建"):
                vals["name"] = seq.next_by_code("sc.treasury.ledger") or _("Ledger")
        return super().create(vals_list)

    @api.constrains("amount")
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("资金流水金额必须大于 0。"))
