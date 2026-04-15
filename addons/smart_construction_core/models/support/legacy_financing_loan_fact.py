# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class ScLegacyFinancingLoanFact(models.Model):
    _name = "sc.legacy.financing.loan.fact"
    _description = "Legacy Financing and Loan Fact"
    _order = "document_date desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(string="摘要", compute="_compute_display_name", store=True)
    legacy_source_table = fields.Char(string="旧系统来源表", required=True, index=True, copy=False)
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True, copy=False)
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    source_family = fields.Selection(
        [
            ("loan_registration", "贷款登记"),
            ("borrowing_request", "借款申请"),
        ],
        string="来源业务家族",
        required=True,
        index=True,
    )
    source_direction = fields.Selection(
        [
            ("financing_in", "融资流入"),
            ("borrowed_fund", "借入/调入资金"),
        ],
        string="来源资金方向",
        required=True,
        index=True,
        help="保留旧系统资金事实方向；不代表付款、结算、凭证或余额状态。",
    )
    document_no = fields.Char(string="旧系统单据号", index=True, copy=False)
    document_date = fields.Date(string="旧系统单据日期", required=True, index=True)
    due_date = fields.Date(string="旧系统到期/还款日期", index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True, copy=False)

    project_id = fields.Many2one(
        "project.project",
        string="项目",
        required=True,
        index=True,
        ondelete="restrict",
        help="旧贷款/借款事实必须锚定项目；缺失或无法确认项目的记录不进入核心资产。",
    )
    legacy_project_id = fields.Char(string="旧系统项目ID", required=True, index=True, copy=False)
    legacy_project_name = fields.Char(string="旧系统项目名称", copy=False)

    partner_id = fields.Many2one(
        "res.partner",
        string="相对方",
        index=True,
        ondelete="restrict",
        help="旧系统相对方已资产化时填充；个人或未资产化对象保留在旧系统相对方名称中。",
    )
    legacy_counterparty_id = fields.Char(string="旧系统相对方ID", index=True, copy=False)
    legacy_counterparty_name = fields.Char(string="旧系统相对方名称", required=True, index=True, copy=False)

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
        help="旧系统贷款或借款金额事实；不生成资金流水或会计结果。",
    )
    source_amount_field = fields.Char(string="金额来源字段", required=True, copy=False)
    purpose = fields.Char(string="旧系统用途/摘要", index=True, copy=False)
    source_type_label = fields.Char(string="旧系统类型/利率/期限", copy=False)
    source_extra_ref = fields.Char(string="旧系统扩展引用ID", index=True, copy=False)
    source_extra_label = fields.Char(string="旧系统扩展引用名称", copy=False)
    note = fields.Text(string="旧系统备注")

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_financing_loan_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_financing_loan_batch",
            "unique(legacy_source_table, legacy_record_id, import_batch)",
            "同一批次中旧系统贷款/借款事实不可重复。",
        )
    ]

    @api.depends("document_no", "source_family", "source_amount", "currency_id", "legacy_counterparty_name")
    def _compute_display_name(self):
        family_labels = dict(self._fields["source_family"].selection)
        for rec in self:
            family = family_labels.get(rec.source_family) or rec.source_family or "旧融资事实"
            amount = rec.source_amount or 0.0
            currency = rec.currency_id.name or ""
            doc = rec.document_no or rec.legacy_record_id or ""
            counterparty = rec.legacy_counterparty_name or ""
            rec.display_name = "%s / %s / %s / %.2f %s" % (family, doc, counterparty, amount, currency)

    @api.constrains("source_amount")
    def _check_source_amount_positive(self):
        for rec in self:
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            if float_compare(rec.source_amount or 0.0, 0.0, precision_rounding=rounding) <= 0:
                raise ValidationError("贷款/借款来源金额必须大于 0。")

    @api.constrains("legacy_project_id", "project_id")
    def _check_project_anchor(self):
        for rec in self:
            if not rec.project_id or not (rec.legacy_project_id or "").strip():
                raise ValidationError("贷款/借款旧业务事实必须保留项目锚点。")

    @api.constrains("legacy_counterparty_name", "partner_id")
    def _check_counterparty_evidence(self):
        for rec in self:
            if not rec.partner_id and not (rec.legacy_counterparty_name or "").strip():
                raise ValidationError("贷款/借款旧业务事实必须保留相对方名称或资产化相对方。")
