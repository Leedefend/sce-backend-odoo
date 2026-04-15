# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ScLegacyReceiptIncomeFact(models.Model):
    _name = "sc.legacy.receipt.income.fact"
    _description = "Legacy Receipt and Income Fact"
    _order = "document_date desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(string="摘要", compute="_compute_display_name", store=True)
    legacy_source_table = fields.Char(string="旧系统来源表", required=True, index=True, copy=False)
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True, copy=False)
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    source_family = fields.Selection(
        [
            ("customer_receipt", "甲方回款"),
            ("receipt_confirmation", "到款确认"),
            ("company_financial_income", "公司财务收入"),
        ],
        string="来源业务家族",
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("inflow", "收入")],
        string="来源方向",
        required=True,
        index=True,
        help="保留旧业务方向，仅用于事实分类；不生成收付款运行态、会计或结算状态。",
    )
    document_no = fields.Char(string="旧系统单据号", index=True, copy=False)
    document_date = fields.Date(string="旧系统单据日期", index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True, copy=False)
    income_category = fields.Char(string="旧系统收入类别", index=True, copy=False)

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="restrict",
        help="剩余收入旧业务事实必须锚定项目；缺失或无法确认项目的记录不进入核心资产。",
    )
    legacy_project_id = fields.Char(string="旧系统项目ID", required=True, index=True, copy=False)
    legacy_project_name = fields.Char(string="旧系统项目名称", copy=False)
    partner_id = fields.Many2one(
        "res.partner",
        string="相对方",
        index=True,
        ondelete="restrict",
        help="旧系统相对方已资产化时填充；否则保留相对方名称文本。",
    )
    legacy_partner_id = fields.Char(string="旧系统相对方ID", index=True, copy=False)
    legacy_partner_name = fields.Char(string="旧系统相对方名称", index=True, copy=False)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    source_amount = fields.Monetary(
        string="来源金额",
        currency_field="currency_id",
        required=True,
        help="旧表中的收入金额事实；不代表 payment.request、account.move 或结算完成。",
    )
    note = fields.Text(string="旧系统备注")

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_receipt_income_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_receipt_income_batch",
            "unique(legacy_source_table, legacy_record_id, import_batch)",
            "同一批次中旧系统收入事实不可重复。",
        )
    ]

    @api.depends("legacy_source_table", "document_no", "source_family", "source_amount", "currency_id")
    def _compute_display_name(self):
        family_labels = dict(self._fields["source_family"].selection)
        for rec in self:
            family = family_labels.get(rec.source_family) or rec.source_family or "旧收入事实"
            amount = rec.source_amount or 0.0
            currency = rec.currency_id.name or ""
            doc = rec.document_no or rec.legacy_record_id or ""
            rec.display_name = "%s / %s / %.2f %s" % (family, doc, amount, currency)

    @api.constrains("source_amount")
    def _check_source_amount_positive(self):
        for rec in self:
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            if float_compare(rec.source_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("收入来源金额必须大于 0。")

    @api.constrains("legacy_project_id", "project_id")
    def _check_project_anchor(self):
        for rec in self:
            if not rec.project_id or not (rec.legacy_project_id or "").strip():
                raise ValidationError("收入旧业务事实必须保留项目锚点。")
