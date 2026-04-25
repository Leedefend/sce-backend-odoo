# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFinancingLoanFact(models.Model):
    _name = "sc.legacy.financing.loan.fact"
    _description = "Legacy Financing Loan Fact"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(string="历史来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="历史记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="历史附件PID", index=True)
    source_family = fields.Char(string="来源族类", index=True)
    source_direction = fields.Char(string="资金方向", index=True)
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Date(string="业务日期", index=True)
    legacy_state = fields.Char(string="历史状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(string="历史项目ID", index=True)
    legacy_project_name = fields.Char(string="历史项目名称")
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_counterparty_id = fields.Char(string="历史往来方ID", index=True)
    legacy_counterparty_name = fields.Char(string="历史往来方名称")
    source_amount = fields.Float(string="金额")
    source_amount_field = fields.Char(string="金额来源字段")
    purpose = fields.Text(string="用途说明")
    source_type_label = fields.Char(string="来源类型")
    source_extra_ref = fields.Char(string="扩展引用")
    source_extra_label = fields.Char(string="扩展标签")
    due_date = fields.Date(string="到期日", index=True)
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", required=True, index=True)
