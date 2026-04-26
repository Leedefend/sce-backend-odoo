# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScFinancingLoan(models.Model):
    _name = "sc.financing.loan"
    _description = "Financing and Borrowing Registration"
    _order = "document_date desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    loan_type = fields.Selection(
        [
            ("loan_registration", "贷款登记"),
            ("borrowing_request", "借款申请"),
        ],
        string="业务类型",
        default="loan_registration",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("financing_in", "融资流入"), ("borrowed_fund", "借入资金")],
        string="资金方向",
        default="financing_in",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("done", "已完成"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    document_no = fields.Char(string="来源单号", index=True)
    document_date = fields.Date(string="业务日期", default=fields.Date.context_today, index=True)
    due_date = fields.Date(string="到期日", index=True)
    amount = fields.Monetary(string="金额", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    purpose = fields.Text(string="用途说明")
    rate_label = fields.Char(string="利率/类型", index=True)
    extra_ref = fields.Char(string="扩展引用", index=True)
    extra_label = fields.Char(string="扩展标签", index=True)
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    legacy_counterparty_id = fields.Char(string="历史往来方ID", index=True, readonly=True)
    legacy_counterparty_name = fields.Char(string="历史往来方", index=True, readonly=True)
    legacy_amount_field = fields.Char(string="历史金额字段", index=True, readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy financing loan source must be unique.",
        ),
        ("amount_nonnegative", "CHECK(amount >= 0)", "Financing loan amount must be non-negative."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.financing.loan") or _("Financing Loan")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"partner_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移融资/借款单据已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirmed"

    def action_done(self):
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                rec.state = "done"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移融资/借款单据不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"
