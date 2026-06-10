# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


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
    deduction_flow_label = fields.Char(string="办理事项", compute="_compute_deduction_flow_label")
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
    deduction_unit_name = fields.Char(string="扣款单位", index=True)
    withholding_amount = fields.Monetary(string="扣款金额", currency_field="currency_id")
    deduction_reason = fields.Text(string="扣款事由")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "sc_tax_deduction_registration_attachment_rel",
        "registration_id",
        "attachment_id",
        string="附件",
    )
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

    @api.model
    def _context_project_id(self):
        project_id = self.env.context.get("default_project_id") or self.env.context.get("current_project_id")
        try:
            return int(project_id) if project_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def _context_partner_id(self):
        partner_id = self.env.context.get("default_partner_id") or self.env.context.get("current_partner_id")
        try:
            return int(partner_id) if partner_id else False
        except (TypeError, ValueError):
            return False

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        project_id = res.get("project_id") or self._context_project_id()
        if project_id and "project_id" in fields_list:
            res["project_id"] = project_id
        partner_id = res.get("partner_id") or self._context_partner_id()
        if partner_id and "partner_id" in fields_list:
            res["partner_id"] = partner_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            project_id = self._context_project_id()
            if project_id:
                vals.setdefault("project_id", project_id)
            partner_id = self._context_partner_id()
            if partner_id:
                vals.setdefault("partner_id", partner_id)
            context_date = self.env.context.get("default_document_date") or self.env.context.get("current_document_date")
            if context_date:
                vals.setdefault("document_date", context_date)
            context_deduction_amount = self.env.context.get("default_deduction_amount") or self.env.context.get("default_amount")
            if context_deduction_amount:
                vals.setdefault("deduction_amount", context_deduction_amount)
            context_tax_amount = self.env.context.get("default_deduction_tax_amount")
            if context_tax_amount:
                vals.setdefault("deduction_tax_amount", context_tax_amount)
            context_note = self.env.context.get("default_note")
            if context_note:
                vals.setdefault("note", context_note)
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

    @api.depends("is_transfer_out", "withholding_amount", "deduction_tax_amount", "deduction_amount")
    def _compute_deduction_flow_label(self):
        for rec in self:
            if rec.is_transfer_out:
                rec.deduction_flow_label = _("进项税额转出")
            elif rec.withholding_amount:
                rec.deduction_flow_label = _("扣款抵扣")
            elif rec.deduction_tax_amount or rec.deduction_amount:
                rec.deduction_flow_label = _("进项税额抵扣")
            else:
                rec.deduction_flow_label = _("抵扣登记")

    def write(self, vals):
        if any(rec.source_origin == "legacy" and rec.state == "legacy_confirmed" for rec in self):
            allowed = {
                "partner_id",
                "note",
                "active",
                "creator_legacy_user_id",
                "creator_name",
                "created_time",
                "deduction_unit_name",
                "withholding_amount",
                "deduction_reason",
                "attachment_ids",
                "write_uid",
                "write_date",
            }
            if set(vals) - allowed:
                raise UserError(_("历史迁移抵扣登记已确认，只允许补充往来单位和备注。"))
        return super().write(vals)

    def action_confirm(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("只有草稿状态的抵扣登记可以确认。"))
            rec.write({"state": "confirmed"})

    def action_deduct(self):
        for rec in self:
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的抵扣登记可以确认抵扣。"))
            vals = {}
            if not rec.deduction_confirm_date:
                vals["deduction_confirm_date"] = fields.Date.context_today(rec)
            if not rec.deduction_amount and rec.invoice_amount_untaxed:
                vals["deduction_amount"] = rec.invoice_amount_untaxed
            if not rec.deduction_tax_amount and rec.invoice_tax_amount:
                vals["deduction_tax_amount"] = rec.invoice_tax_amount
            if vals:
                rec.write(vals)
            rec._check_deduct_ready()
            rec.write({"state": "deducted"})

    def _check_deduct_ready(self):
        for rec in self:
            if not rec.invoice_no:
                raise UserError(_("请先填写发票号码后再确认抵扣。"))
            if not rec.deduction_confirm_date:
                raise UserError(_("请先填写认证抵扣日期后再确认抵扣。"))
            rounding = rec.currency_id.rounding if rec.currency_id else 0.01
            if float_compare(rec.deduction_tax_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise UserError(_("抵扣税额必须大于 0。"))
            if rec.invoice_tax_amount and float_compare(
                rec.deduction_tax_amount or 0.0,
                rec.invoice_tax_amount or 0.0,
                precision_rounding=rounding,
            ) == 1:
                raise UserError(_("抵扣税额不能超过发票税额。"))
            if rec.invoice_amount_untaxed and rec.deduction_amount and float_compare(
                rec.deduction_amount or 0.0,
                rec.invoice_amount_untaxed or 0.0,
                precision_rounding=rounding,
            ) == 1:
                raise UserError(_("抵扣金额不能超过发票不含税金额。"))

    def action_cancel(self):
        for rec in self:
            if rec.source_origin == "legacy":
                raise UserError(_("历史迁移抵扣登记不能在新系统取消。"))
            if rec.state not in ("draft", "confirmed"):
                raise UserError(_("只有草稿或已确认状态的抵扣登记可以取消。"))
            rec.write({"state": "cancel"})
