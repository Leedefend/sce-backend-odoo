# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyAccountTransactionLine(models.Model):
    _name = "sc.legacy.account.transaction.line"
    _description = "历史账户收支来源明细"
    _order = "transaction_date desc, source_table, legacy_record_id, direction"

    source_key = fields.Char(string="来源键", required=True, index=True)
    source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    document_no = fields.Char(string="单据编号", index=True)
    transaction_date = fields.Date(string="发生日期", index=True)
    document_state = fields.Char(string="单据状态", index=True)
    deleted_flag = fields.Char(string="删除标记", index=True)
    project_legacy_id = fields.Char(string="项目原编号", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    account_legacy_id = fields.Char(string="账户原编号", required=True, index=True)
    account_id = fields.Many2one("sc.legacy.account.master", string="账户", index=True, ondelete="set null")
    account_name = fields.Char(string="账户名称", index=True)
    counterparty_account_legacy_id = fields.Char(string="对方账户原编号", index=True)
    counterparty_account_name = fields.Char(string="对方账户名称", index=True)
    direction = fields.Selection(
        [("income", "收入"), ("expense", "支出")],
        string="方向",
        required=True,
        index=True,
    )
    metric_bucket = fields.Selection(
        [("account_transfer", "账户往来"), ("cumulative", "累计收支")],
        string="统计口径",
        required=True,
        default="account_transfer",
        index=True,
    )
    amount = fields.Float(string="金额")
    category = fields.Char(string="类别", index=True)
    source_summary = fields.Char(string="来源摘要", index=True)
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", default="legacy_account_transaction_v1", required=True, index=True)
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        ("source_key_unique", "unique(source_key)", "Legacy account transaction line must be unique."),
    ]
