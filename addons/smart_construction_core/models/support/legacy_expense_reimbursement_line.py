# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyExpenseReimbursementLine(models.Model):
    _name = "sc.legacy.expense.reimbursement.line"
    _description = "Legacy Expense Reimbursement Line Fact"
    _order = "document_date desc, legacy_line_id"

    legacy_line_id = fields.Char(required=True, index=True)
    legacy_header_id = fields.Char(index=True)
    legacy_pid = fields.Char(index=True)
    legacy_header_pid = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Char(index=True)
    document_state = fields.Char(index=True)
    company_legacy_id = fields.Char(index=True)
    company_name = fields.Char(index=True)
    department_legacy_id = fields.Char(index=True)
    department_name = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    applicant_legacy_id = fields.Char(index=True)
    applicant_name = fields.Char(index=True)
    applicant_contact = fields.Char()
    applicant_position = fields.Char(index=True)
    reimbursement_type_legacy_id = fields.Char(index=True)
    reimbursement_type = fields.Char(index=True)
    finance_type_legacy_id = fields.Char(index=True)
    finance_type = fields.Char(index=True)
    line_project_legacy_id = fields.Char(index=True)
    line_project_name = fields.Char(index=True)
    line_date = fields.Char(index=True)
    amount = fields.Float(index=True)
    quantity = fields.Float()
    unit_price = fields.Float()
    allocated_amount = fields.Float()
    summary = fields.Char(index=True)
    participant = fields.Char(index=True)
    participant_count = fields.Char(index=True)
    deducted_participant = fields.Char(index=True)
    deducted_count = fields.Char(index=True)
    invoice_content = fields.Char(index=True)
    payment_method = fields.Char(index=True)
    payee = fields.Char(index=True)
    payee_account = fields.Char(index=True)
    payee_bank = fields.Char(index=True)
    header_total = fields.Float()
    requested_amount = fields.Float()
    approved_amount = fields.Float()
    writeoff_amount = fields.Float()
    advance_amount = fields.Float()
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    modifier_legacy_user_id = fields.Char(index=True)
    modifier_name = fields.Char(index=True)
    modified_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    line_attachment_ref = fields.Char()
    note = fields.Text()
    header_note = fields.Text()
    source_table = fields.Char(default="CWGL_FYBX_CB", required=True, index=True)
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        ("legacy_expense_reimbursement_line_unique", "unique(legacy_line_id)", "Legacy expense reimbursement line id must be unique."),
    ]
