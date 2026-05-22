# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyReceiptIncomeFact(models.Model):
    _name = "sc.legacy.receipt.income.fact"
    _description = "历史收款收入事实"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(string="旧库来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="旧库记录", required=True, index=True)
    legacy_pid = fields.Char(string="旧库序号", index=True)
    source_family = fields.Char(string="来源类别", index=True)
    direction = fields.Char(string="收支方向", index=True)
    document_no = fields.Char(string="单据编号", index=True)
    document_date = fields.Date(string="单据日期", index=True)
    legacy_state = fields.Char(string="旧库状态", index=True)
    receipt_type = fields.Char(string="收款类型", index=True)
    receipt_subtype = fields.Char(string="收款细分", index=True)
    income_category = fields.Char(string="收入类别", index=True)
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(string="旧库项目", index=True)
    legacy_project_name = fields.Char(string="旧库项目名称")
    partner_id = fields.Many2one("res.partner", string="往来单位", index=True, ondelete="set null")
    legacy_partner_id = fields.Char(string="旧库往来单位")
    legacy_partner_name = fields.Char(string="旧库往来单位名称")
    source_amount = fields.Float(string="原始金额")
    creator_legacy_user_id = fields.Char(string="历史录入人ID", index=True)
    creator_name = fields.Char(string="历史录入人", index=True)
    created_time = fields.Datetime(string="历史录入时间", index=True)
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", required=True, index=True)
