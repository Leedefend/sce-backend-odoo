# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyExpenseDepositFact(models.Model):
    _name = "sc.legacy.expense.deposit.fact"
    _description = "历史费用/保证金事实"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(string="旧系统来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="旧系统记录ID", required=True, index=True)
    legacy_pid = fields.Char(string="旧系统PID", index=True)
    source_family = fields.Char(string="来源类型", index=True)
    direction = fields.Char(string="收支方向", index=True)
    document_no = fields.Char(string="单号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    legacy_state = fields.Char(string="旧系统状态", index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(string="旧系统项目ID", index=True)
    legacy_project_name = fields.Char(string="旧系统项目名称")
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_partner_id = fields.Char(string="旧系统往来单位ID", index=True)
    legacy_partner_name = fields.Char(string="旧系统往来单位名称")
    source_amount = fields.Float(string="金额")
    source_amount_field = fields.Char(string="金额来源字段", index=True)
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", required=True, index=True)
