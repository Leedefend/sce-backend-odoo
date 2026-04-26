# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFundConfirmationLine(models.Model):
    _name = "sc.legacy.fund.confirmation.line"
    _description = "Legacy Fund Confirmation Line Fact"
    _order = "receipt_time desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    document_no = fields.Char(index=True)
    period_no = fields.Char(index=True)
    receipt_time = fields.Datetime(index=True)
    contract_legacy_id = fields.Char(index=True)
    contract_name = fields.Char(index=True)
    contract_amount = fields.Float()
    bid_date = fields.Datetime(index=True)
    current_project_stage = fields.Char(index=True)
    actual_fund_amount = fields.Float()
    accumulated_invoice_amount = fields.Float()
    filler_name = fields.Char(index=True)
    document_state = fields.Char(index=True)
    confirmation_item_legacy_id = fields.Char(index=True)
    confirmation_item_name = fields.Char(index=True)
    ratio = fields.Float()
    current_actual_amount = fields.Float()
    accumulated_actual_amount = fields.Float()
    returned_flag = fields.Char(index=True)
    settlement_basis_flag = fields.Char(index=True)
    settlement_basis_text = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    related_receipt_ids = fields.Text()
    application_balance_note = fields.Text()
    invoice_receipt_note = fields.Text()
    quality_return_note = fields.Text()
    available_balance_note = fields.Text()
    construction_deduction_note = fields.Text()
    payable_construction_deduction_note = fields.Text()
    attachment_ref = fields.Char()
    note = fields.Text()
    source_table = fields.Char(default="ZJGL_SZQR_DKQRB_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_fund_confirmation_line_unique", "unique(legacy_line_id)", "Legacy fund confirmation line id must be unique."),
    ]
