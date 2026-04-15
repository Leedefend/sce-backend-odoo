# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_is_zero


class ScLegacyFundDailySnapshotFact(models.Model):
    _name = "sc.legacy.fund.daily.snapshot.fact"
    _description = "Legacy Fund Daily Snapshot Fact"
    _order = "snapshot_date desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(string="摘要", compute="_compute_display_name", store=True)
    legacy_source_table = fields.Char(
        string="旧系统来源表",
        required=True,
        default="D_SCBSJS_ZJGL_ZJSZ_ZJRBB",
        index=True,
        copy=False,
    )
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True, copy=False)
    legacy_pid = fields.Char(string="旧系统PID", index=True, copy=False)
    source_family = fields.Selection(
        [("fund_daily_balance_snapshot", "资金日报余额快照")],
        string="来源业务家族",
        required=True,
        default="fund_daily_balance_snapshot",
        index=True,
    )
    document_no = fields.Char(string="旧系统单据号", index=True, copy=False)
    snapshot_date = fields.Date(string="资金日报日期", required=True, index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True, copy=False)
    subject = fields.Char(string="旧系统标题", index=True, copy=False)

    project_id = fields.Many2one(
        "project.project",
        string="项目/管理主体",
        required=True,
        index=True,
        ondelete="restrict",
        help="资金日报必须保留旧系统项目或管理主体锚点；缺失或无法确认的记录不进入资产。",
    )
    legacy_project_id = fields.Char(string="旧系统项目ID", required=True, index=True, copy=False)
    legacy_project_name = fields.Char(string="旧系统项目名称", copy=False)

    currency_id = fields.Many2one(
        "res.currency",
        string="币种",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    source_account_balance_total = fields.Monetary(
        string="账户余额合计",
        currency_field="currency_id",
        help="旧系统 ZHYEHJ。仅代表日报快照金额，不生成资金流水或会计余额。",
    )
    source_bank_balance_total = fields.Monetary(
        string="银行余额合计",
        currency_field="currency_id",
        help="旧系统 ZHYHYEHJ。仅代表日报快照金额，不生成资金流水或会计余额。",
    )
    source_bank_system_difference = fields.Monetary(
        string="银行系统差额合计",
        currency_field="currency_id",
        help="旧系统 YHXTCEHJ。允许为负数，仅表示旧日报快照差额。",
    )
    note = fields.Text(string="旧系统备注")

    import_batch = fields.Char(
        string="导入批次",
        default="legacy_fund_daily_snapshot_asset_v1",
        required=True,
        index=True,
        copy=False,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "uniq_legacy_fund_daily_snapshot_batch",
            "unique(legacy_source_table, legacy_record_id, import_batch)",
            "同一批次中旧系统资金日报快照不可重复。",
        )
    ]

    @api.depends(
        "document_no",
        "snapshot_date",
        "source_account_balance_total",
        "currency_id",
    )
    def _compute_display_name(self):
        for rec in self:
            doc = rec.document_no or rec.legacy_record_id or ""
            date = rec.snapshot_date or ""
            amount = rec.source_account_balance_total or 0.0
            currency = rec.currency_id.name or ""
            rec.display_name = "资金日报 / %s / %s / %.2f %s" % (doc, date, amount, currency)

    @api.constrains("legacy_project_id", "project_id")
    def _check_project_anchor(self):
        for rec in self:
            if not rec.project_id or not (rec.legacy_project_id or "").strip():
                raise ValidationError("资金日报旧业务事实必须保留项目或管理主体锚点。")

    @api.constrains(
        "source_account_balance_total",
        "source_bank_balance_total",
        "source_bank_system_difference",
    )
    def _check_snapshot_amount_present(self):
        for rec in self:
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            values = [
                rec.source_account_balance_total or 0.0,
                rec.source_bank_balance_total or 0.0,
                rec.source_bank_system_difference or 0.0,
            ]
            if all(float_is_zero(value, precision_rounding=rounding) for value in values):
                raise ValidationError("资金日报快照至少需要一个非零余额或差额。")
