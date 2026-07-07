# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceTaxFact(models.Model):
    _name = "sc.legacy.invoice.tax.fact"
    _description = "历史发票税额事实"
    _order = "document_date desc, id desc"

    legacy_source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    source_family = fields.Char(index=True)
    direction = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Date(index=True)
    document_state_text = fields.Char(string="状态", index=True)
    legacy_state = fields.Char(index=True)
    invoice_type = fields.Char(index=True)
    invoice_no = fields.Char(index=True)
    invoice_company_type = fields.Char(index=True)
    invoice_issue_company = fields.Char(index=True)
    invoice_provider_name = fields.Char(index=True)
    invoice_partner_name = fields.Char(string="开票单位", index=True)
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(index=True)
    legacy_project_name = fields.Char()
    legacy_partner_id = fields.Char(index=True)
    legacy_partner_name = fields.Char()
    legacy_partner_tax_no = fields.Char(index=True)
    amount_untaxed = fields.Float(string="不含税金额")
    amount_total = fields.Float(string="价税合计")
    tax_amount = fields.Float(string="税额")
    source_amount_untaxed = fields.Float()
    source_amount = fields.Float()
    source_tax_amount = fields.Float()
    source_amount_field = fields.Char(index=True)
    attachment_ref = fields.Char(string="附件引用", index=True)
    push_result = fields.Char(index=True)
    kingdee_document_no = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    note = fields.Text()
    import_batch = fields.Char(required=True, index=True)
