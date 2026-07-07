# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFundConfirmationHeader(models.Model):
    _name = "sc.legacy.fund.confirmation.header"
    _description = "历史资金确认主表事实"
    _order = "receipt_time desc, document_no desc, legacy_header_id"

    legacy_header_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
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
    attachment_ref = fields.Char(index=True)
    note = fields.Text()
    source_table = fields.Char(default="ZJGL_SZQR_DKQRB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "legacy_fund_confirmation_header_unique",
            "unique(legacy_header_id)",
            "历史资金确认主表记录必须唯一。",
        ),
    ]
