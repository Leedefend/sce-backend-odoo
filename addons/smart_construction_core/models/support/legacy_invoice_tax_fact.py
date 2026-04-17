# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ScLegacyInvoiceTaxFact(models.Model):
    _name = "sc.legacy.invoice.tax.fact"
    _description = "Legacy Invoice and Tax Fact"
    _order = "document_date desc, id desc"
    _rec_name = "display_name"

    def _manual_entry_source_table(self):
        return "manual.sc.legacy.invoice.tax.fact"

    def _apply_manual_entry_defaults(self, vals):
        if vals.get("legacy_source_table") and vals.get("legacy_record_id"):
            return vals
        vals = dict(vals)
        vals.setdefault("legacy_source_table", self._manual_entry_source_table())
        vals.setdefault("legacy_record_id", "MANUAL-%s" % uuid4().hex)
        vals.setdefault("source_amount_field", "manual_source_amount")
        project_id = vals.get("project_id")
        if project_id and not vals.get("legacy_project_id"):
            project = self.env["project.project"].browse(project_id)
            vals["legacy_project_id"] = project.legacy_project_id or project.project_code or str(project.id)
            vals.setdefault("legacy_project_name", project.name)
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([self._apply_manual_entry_defaults(vals) for vals in vals_list])

    display_name = fields.Char(string="摘要", compute="_compute_display_name", store=True)
    legacy_source_table = fields.Char(string="旧系统来源表", required=True, index=True, copy=False)
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True, copy=False)
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    source_family = fields.Selection(
        [
            ("input_invoice_handover", "进项发票交接"),
            ("output_invoice_register", "销项开票登记"),
            ("invoice_issue_request", "开具发票申请"),
            ("prepaid_tax_register", "预缴税款登记"),
        ],
        string="来源业务家族",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [
            ("input_invoice", "进项发票"),
            ("output_invoice", "销项发票"),
            ("prepaid_tax", "预缴税款"),
        ],
        string="来源方向",
        required=True,
        index=True,
        help="保留旧业务方向，仅用于事实分类；不生成会计、税务台账、收付款或结算状态。",
    )
    document_no = fields.Char(string="旧系统单据号", index=True, copy=False)
    document_date = fields.Date(string="旧系统单据日期", index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True, copy=False)
    invoice_type = fields.Char(string="旧系统票据/税务类型", index=True, copy=False)

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="restrict",
        help="旧发票/税务事实必须锚定项目；缺失或无法确认项目的记录不进入核心资产。",
    )
    legacy_project_id = fields.Char(string="旧系统项目ID", required=True, index=True, copy=False)
    legacy_project_name = fields.Char(string="旧系统项目名称", copy=False)
    partner_id = fields.Many2one(
        "res.partner",
        string="相对方",
        index=True,
        ondelete="restrict",
        help="旧系统相对方已资产化时填充；否则保留相对方名称和税号文本。",
    )
    legacy_partner_id = fields.Char(string="旧系统相对方ID", index=True, copy=False)
    legacy_partner_name = fields.Char(string="旧系统相对方名称", index=True, copy=False)
    legacy_partner_tax_no = fields.Char(string="旧系统相对方税号", index=True, copy=False)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    source_amount = fields.Monetary(
        string="来源价税/开票金额",
        currency_field="currency_id",
        help="旧表中的发票或税务金额事实；不代表 account.move、税务申报或付款完成。",
    )
    source_tax_amount = fields.Monetary(
        string="来源税额",
        currency_field="currency_id",
        help="旧表中的税额事实；不生成税务台账状态。",
    )
    source_amount_field = fields.Char(string="金额来源字段", required=True, copy=False)
    note = fields.Text(string="旧系统备注")

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_invoice_tax_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_invoice_tax_batch",
            "unique(legacy_source_table, legacy_record_id, import_batch)",
            "同一批次中旧系统发票/税务事实不可重复。",
        )
    ]

    @api.depends("legacy_source_table", "document_no", "source_family", "source_amount", "source_tax_amount", "currency_id")
    def _compute_display_name(self):
        family_labels = dict(self._fields["source_family"].selection)
        for rec in self:
            family = family_labels.get(rec.source_family) or rec.source_family or "旧发票税务事实"
            amount = rec.source_amount or rec.source_tax_amount or 0.0
            currency = rec.currency_id.name or ""
            doc = rec.document_no or rec.legacy_record_id or ""
            rec.display_name = "%s / %s / %.2f %s" % (family, doc, amount, currency)

    @api.constrains("source_amount", "source_tax_amount")
    def _check_source_amount_or_tax_positive(self):
        for rec in self:
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            amount = max(rec.source_amount or 0.0, rec.source_tax_amount or 0.0)
            if float_compare(amount, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("发票/税务来源金额或税额至少一项必须大于 0。")

    @api.constrains("legacy_project_id", "project_id")
    def _check_project_anchor(self):
        for rec in self:
            if not rec.project_id or not (rec.legacy_project_id or "").strip():
                raise ValidationError("发票/税务旧业务事实必须保留项目锚点。")

    @api.constrains("legacy_partner_name", "legacy_partner_tax_no", "partner_id")
    def _check_counterparty_evidence(self):
        for rec in self:
            has_name = bool((rec.legacy_partner_name or "").strip())
            has_tax_no = bool((rec.legacy_partner_tax_no or "").strip())
            if not rec.partner_id and not has_name and not has_tax_no:
                raise ValidationError("发票/税务旧业务事实必须保留相对方名称、税号或资产化相对方。")
