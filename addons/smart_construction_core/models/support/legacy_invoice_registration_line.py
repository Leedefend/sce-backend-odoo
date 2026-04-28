# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyInvoiceRegistrationLine(models.Model):
    _name = "sc.legacy.invoice.registration.line"
    _description = "Legacy Invoice Registration Line Fact"
    _order = "invoice_date desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    fee_project_legacy_id = fields.Char(index=True)
    fee_project_name = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Datetime(index=True)
    invoice_date = fields.Datetime(index=True)
    recognition_date = fields.Datetime(index=True)
    invoice_no = fields.Char(index=True)
    invoice_code = fields.Char(index=True)
    invoice_type = fields.Char(string="Invoice Type Name", index=True)
    invoice_type_id = fields.Char(string="Invoice Type Legacy ID", index=True)
    supplier_legacy_id = fields.Char(index=True)
    supplier_name = fields.Char(index=True)
    supplier_tax_no = fields.Char(index=True)
    partner_id = fields.Many2one("res.partner", index=True, ondelete="set null")
    amount_no_tax = fields.Float()
    tax_amount = fields.Float()
    amount_total = fields.Float()
    tax_rate = fields.Char(string="Tax Rate Text", index=True)
    tax_rate_id = fields.Char(string="Tax Rate Legacy ID", index=True)
    quantity = fields.Float()
    invoice_content = fields.Char(index=True)
    cost_category_id = fields.Char(index=True)
    cost_category_name = fields.Char(index=True)
    contract_legacy_id = fields.Char(index=True)
    settlement_legacy_id = fields.Char(index=True)
    related_invoice_line_id = fields.Char(index=True)
    related_invoice_line_no = fields.Char(index=True)
    handler_name = fields.Char(index=True)
    header_state = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modified_time = fields.Datetime(index=True)
    invoice_holder = fields.Char(index=True)
    accounting_state = fields.Char(index=True)
    checksum = fields.Char(index=True)
    voucher_no = fields.Char(index=True)
    invoice_source = fields.Char(index=True)
    project_cost_amount = fields.Float()
    billing_unit = fields.Char(index=True)
    attachment_ref = fields.Char()
    attachment_name = fields.Char()
    attachment_path = fields.Char()
    note = fields.Text()
    source_table = fields.Char(default="C_JXXP_ZYFPJJD_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_invoice_registration_line_unique", "unique(legacy_line_id)", "Legacy invoice registration line id must be unique."),
    ]
