# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacySelfFundingFact(models.Model):
    _name = "sc.legacy.self.funding.fact"
    _description = "历史自筹资金事实"
    _order = "document_date desc, source_table, legacy_record_id"

    source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_header_id = fields.Char(string="历史主表ID", index=True)
    legacy_pid = fields.Char(string="历史PID", index=True)
    line_type = fields.Selection(
        [("income", "自筹收入"), ("refund", "自筹退回")],
        string="类型",
        required=True,
        index=True,
    )
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    document_state = fields.Char(string="历史状态", index=True)
    deleted_flag = fields.Char(string="删除标记", index=True)
    project_legacy_id = fields.Char(string="历史项目ID", index=True)
    project_name = fields.Char(string="项目名称", index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(string="历史往来单位ID", index=True)
    partner_name = fields.Char(string="往来单位", index=True)
    partner_id = fields.Many2one("res.partner", string="往来单位记录", index=True, ondelete="set null")
    income_category = fields.Char(string="收入类别", index=True)
    receipt_type = fields.Char(string="收款类型", index=True)
    legacy_category = fields.Char(string="历史分类", index=True)
    self_funding_amount = fields.Float(string="自筹收入金额")
    refund_amount = fields.Float(string="自筹退回金额")
    unreturned_amount = fields.Float(string="自筹未退金额")
    payment_method = fields.Char(string="收款/退回方式", index=True)
    account_name = fields.Char(string="账户", index=True)
    import_batch = fields.Char(string="导入批次", default="legacy_self_funding_v1", required=True, index=True)
    note = fields.Text(string="备注")
    active = fields.Boolean(string="有效", default=True, index=True)

    _sql_constraints = [
        (
            "legacy_self_funding_unique",
            "unique(source_table, legacy_record_id, line_type)",
            "Legacy self funding fact must be unique.",
        ),
    ]
