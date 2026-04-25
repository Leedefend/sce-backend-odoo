# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceTaxFact(models.Model):
    _name = "sc.legacy.invoice.tax.fact"
    _description = "Legacy Invoice Tax Fact"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    source_family = fields.Char(index=True)
    direction = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Date(index=True)
    legacy_state = fields.Char(index=True)
    invoice_type = fields.Char(index=True)
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(index=True)
    legacy_project_name = fields.Char()
    legacy_partner_id = fields.Char(index=True)
    legacy_partner_name = fields.Char()
    legacy_partner_tax_no = fields.Char(index=True)
    source_amount = fields.Float()
    source_tax_amount = fields.Float()
    source_amount_field = fields.Char(index=True)
    note = fields.Text()
    import_batch = fields.Char(required=True, index=True)
