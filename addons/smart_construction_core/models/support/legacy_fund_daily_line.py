# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFundDailyLine(models.Model):
    _name = "sc.legacy.fund.daily.line"
    _description = "Legacy Fund Daily Account Line Fact"
    _order = "document_date desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Date(index=True)
    document_state = fields.Char(index=True)
    title = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    period_start = fields.Datetime(index=True)
    period_end = fields.Datetime(index=True)
    account_legacy_id = fields.Char(index=True)
    account_name = fields.Char(index=True)
    bank_account_no = fields.Char(index=True)
    account_balance = fields.Float()
    daily_income = fields.Float()
    daily_expense = fields.Float()
    current_account_balance = fields.Float()
    current_bank_balance = fields.Float()
    bank_system_difference = fields.Float()
    header_account_balance_total = fields.Float()
    header_bank_balance_total = fields.Float()
    header_bank_system_difference = fields.Float()
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    line_attachment_ref = fields.Char()
    note = fields.Text()
    header_note = fields.Text()
    source_table = fields.Char(default="D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_fund_daily_line_unique", "unique(legacy_line_id)", "Legacy fund daily line id must be unique."),
    ]
