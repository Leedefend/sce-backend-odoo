# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyReceiptIncomeFact(models.Model):
    _name = "sc.legacy.receipt.income.fact"
    _description = "Legacy Receipt Income Fact"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    source_family = fields.Char(index=True)
    direction = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Date(index=True)
    legacy_state = fields.Char(index=True)
    income_category = fields.Char(index=True)
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(index=True)
    legacy_project_name = fields.Char()
    partner_id = fields.Many2one("res.partner", index=True, ondelete="set null")
    legacy_partner_id = fields.Char(index=True)
    legacy_partner_name = fields.Char()
    source_amount = fields.Float()
    note = fields.Text()
    import_batch = fields.Char(required=True, index=True)
