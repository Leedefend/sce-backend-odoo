# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFinanceAuxiliaryFact(models.Model):
    _name = "sc.legacy.finance.auxiliary.fact"
    _description = "历史财税辅助事实"
    _order = "document_date desc, source_table, legacy_record_id"

    source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_parent_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    fact_type = fields.Char(index=True)
    source_dataset = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Datetime(index=True)
    document_state = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", string="项目", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(index=True)
    partner_name = fields.Char(index=True)
    invoice_code = fields.Char(index=True)
    invoice_no = fields.Char(index=True)
    invoice_type = fields.Char(index=True)
    amount_total = fields.Float()
    amount_no_tax = fields.Float()
    tax_amount = fields.Float()
    tax_rate = fields.Float()
    category_code = fields.Char(index=True)
    category_name = fields.Char(index=True)
    handler_name = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_finance_auxiliary_unique",
            "unique(source_table, legacy_record_id)",
            "同一历史财税辅助事实只能导入一次。",
        ),
    ]
