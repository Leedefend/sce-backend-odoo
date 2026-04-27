# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFundDailyLine(models.Model):
    _name = "sc.legacy.fund.daily.line"
    _description = "资金日报明细"
    _order = "document_date desc, legacy_line_id"

    legacy_line_id = fields.Char(string="明细编号", required=True, index=True)
    legacy_header_id = fields.Char(string="主表编号", index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    legacy_header_pid = fields.Char(string="主表附件编号", index=True)
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Date(string="日期", index=True)
    document_state = fields.Char(string="状态", index=True)
    title = fields.Char(string="标题", index=True)
    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    period_start = fields.Datetime(string="期间开始", index=True)
    period_end = fields.Datetime(string="期间结束", index=True)
    account_legacy_id = fields.Char(string="账户原编号", index=True)
    account_name = fields.Char(string="账户名称", index=True)
    bank_account_no = fields.Char(string="银行账号", index=True)
    account_balance = fields.Float(string="账面余额")
    daily_income = fields.Float(string="当日收入")
    daily_expense = fields.Float(string="当日支出")
    current_account_balance = fields.Float(string="当前账面余额")
    current_bank_balance = fields.Float(string="当前银行余额")
    bank_system_difference = fields.Float(string="账实差异")
    header_account_balance_total = fields.Float(string="主表账面余额合计")
    header_bank_balance_total = fields.Float(string="主表银行余额合计")
    header_bank_system_difference = fields.Float(string="主表账实差异")
    creator_legacy_user_id = fields.Char(string="创建人原编号", index=True)
    creator_name = fields.Char(string="创建人", index=True)
    created_time = fields.Datetime(string="创建时间", index=True)
    modifier_legacy_user_id = fields.Char(string="修改人原编号", index=True)
    modifier_name = fields.Char(string="修改人", index=True)
    modified_time = fields.Datetime(string="修改时间", index=True)
    attachment_ref = fields.Char(string="附件")
    line_attachment_ref = fields.Char(string="明细附件")
    note = fields.Text(string="备注")
    header_note = fields.Text(string="主表备注")
    source_table = fields.Char(string="来源表", default="D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_fund_daily_line_unique", "unique(legacy_line_id)", "Legacy fund daily line id must be unique."),
    ]
