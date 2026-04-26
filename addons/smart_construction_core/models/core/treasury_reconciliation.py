# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScTreasuryReconciliation(models.Model):
    _name = "sc.treasury.reconciliation"
    _description = "Treasury Daily Reconciliation"
    _order = "date_document desc, id desc"

    name = fields.Char(string="单据号", required=True, default="新建", copy=False)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    source_kind = fields.Selection(
        [
            ("daily_line", "资金日报"),
            ("fund_confirmation", "资金确认"),
        ],
        string="业务类型",
        default="daily_line",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("reconciled", "已对账"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    date_document = fields.Date(string="业务日期", default=fields.Date.context_today, required=True, index=True)
    document_no = fields.Char(string="来源单号", index=True)
    account_name = fields.Char(string="账户名称", index=True)
    bank_account_no = fields.Char(string="银行账号", index=True)
    confirmation_item_name = fields.Char(string="确认事项", index=True)
    account_balance = fields.Monetary(string="账面余额", currency_field="currency_id")
    bank_balance = fields.Monetary(string="银行余额", currency_field="currency_id")
    system_difference = fields.Monetary(string="银企差额", currency_field="currency_id")
    daily_income = fields.Monetary(string="本日收入", currency_field="currency_id")
    daily_expense = fields.Monetary(string="本日支出", currency_field="currency_id")
    confirmation_amount = fields.Monetary(string="确认金额", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    treasury_ledger_id = fields.Many2one("sc.treasury.ledger", string="资金台账", index=True, ondelete="set null")
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy treasury reconciliation source must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.treasury.reconciliation") or _("Treasury Reconciliation")
        return super().create(vals_list)

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {"treasury_ledger_id", "note", "active", "write_uid", "write_date"}
            if set(vals) - allowed:
                raise UserError(_("历史迁移资金对账单已确认，只允许补充资金台账关联和备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state == "draft":
                rec.state = "confirmed"

    def action_reconcile(self):
        for rec in self:
            if rec.state in ("draft", "confirmed"):
                rec.state = "reconciled"

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移资金对账单不能在新系统取消。"))
            if rec.state != "cancel":
                rec.state = "cancel"
