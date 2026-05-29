# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ScTaxDeductionRegistration(models.Model):
    _name = "sc.tax.deduction.registration"
    _description = "抵扣登记"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "deduction_confirm_date desc, document_date desc, id desc"

    name = fields.Char(string="登记单号", required=True, default="新建", copy=False, index=True)
    source_origin = fields.Selection(
        [("manual", "新系统登记"), ("legacy", "历史迁移")],
        string="来源",
        default="manual",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "草稿"),
            ("confirmed", "已确认"),
            ("deducted", "已抵扣"),
            ("legacy_confirmed", "历史已确认"),
            ("cancel", "已取消"),
        ],
        string="状态",
        default="draft",
        required=True,
        index=True,
    )
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", default=fields.Date.context_today, index=True)
    deduction_confirm_date = fields.Date(string="认证抵扣日期", index=True)
    legacy_visible_project_name = fields.Char(string="历史可见项目名称", readonly=True, index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True)
    company_id = fields.Many2one(
        "res.company",
        string="公司",
        related="project_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )
    operation_strategy = fields.Selection(
        related="project_id.operation_strategy",
        string="经营方式",
        store=True,
        readonly=True,
        index=True,
    )
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True)
    partner_name = fields.Char(string="历史往来单位", index=True)
    invoice_no = fields.Char(string="发票号码", index=True)
    invoice_code = fields.Char(string="发票代码", index=True)
    invoice_date = fields.Date(string="开票日期", index=True)
    invoice_amount_untaxed = fields.Monetary(string="发票不含税金额", currency_field="currency_id")
    invoice_tax_amount = fields.Monetary(string="发票税额", currency_field="currency_id")
    invoice_amount_total = fields.Monetary(string="发票价税合计", currency_field="currency_id")
    tax_rate_text = fields.Char(
        string="税率",
        compute="_compute_tax_rate_text",
        store=True,
        readonly=True,
        index=True,
    )
    deduction_amount = fields.Monetary(string="抵扣金额", currency_field="currency_id")
    deduction_tax_amount = fields.Monetary(string="抵扣税额", currency_field="currency_id")
    deduction_surcharge_amount = fields.Monetary(string="抵扣附加税", currency_field="currency_id")
    is_transfer_out = fields.Boolean(string="是否转出", default=False, index=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    legacy_source_model = fields.Char(string="历史来源模型", index=True, readonly=True)
    legacy_source_table = fields.Char(string="历史来源表", index=True, readonly=True)
    legacy_record_id = fields.Char(string="历史记录ID", index=True, readonly=True)
    legacy_document_state = fields.Char(string="历史状态", index=True, readonly=True)
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True, readonly=True)
    creator_name = fields.Char(string="历史录入人", index=True, readonly=True)
    created_time = fields.Datetime(string="历史录入时间", index=True, readonly=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_source_unique",
            "unique(legacy_source_model, legacy_record_id)",
            "Legacy tax deduction source must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", "新建") == "新建":
                vals["name"] = seq.next_by_code("sc.tax.deduction.registration") or _("Tax Deduction")
        return super().create(vals_list)

    @api.depends("invoice_amount_untaxed", "invoice_tax_amount")
    def _compute_tax_rate_text(self):
        for record in self:
            untaxed = record.invoice_amount_untaxed or 0.0
            tax = record.invoice_tax_amount or 0.0
            if not untaxed or not tax:
                record.tax_rate_text = False
                continue
            rate = tax / untaxed * 100
            record.tax_rate_text = f"{rate:.2f}".rstrip("0").rstrip(".") + "%"

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "partner_id",
                "note",
                "active",
                "creator_legacy_user_id",
                "creator_name",
                "created_time",
                "write_uid",
                "write_date",
            }
            if set(vals) - allowed:
                raise UserError(_("历史迁移抵扣登记已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    def action_confirm(self):
        self.filtered(lambda rec: rec.state == "draft").write({"state": "confirmed"})

    def action_deduct(self):
        self.filtered(lambda rec: rec.state in ("draft", "confirmed")).write({"state": "deducted"})

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移抵扣登记不能在新系统取消。"))
        self.filtered(lambda rec: rec.state != "cancel").write({"state": "cancel"})
