# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


EXPENSE_TYPE_LABELS = {
    "advance_fund": "备用金",
    "repayment_form": "还款单",
    "project_expense_claim": "项目费用报销单",
}


def _map_expense_state(record):
    if record.state == "done":
        return "done"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "approved"
    return "draft"


def _map_loan_state(record):
    if record.state == "done":
        return "done"
    if record.state == "cancel":
        return "cancel"
    if record.state == "in_progress":
        return "confirmed"
    return "draft"


def _migrate_expense_claims(env):
    Source = env["sc.finance.expense.document"].sudo()
    Claim = env["sc.expense.claim"].sudo()
    records = Source.search([("fact_type", "in", list(EXPENSE_TYPE_LABELS)), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Claim.search([("legacy_source_model", "=", record._name), ("legacy_record_id", "=", str(record.id))], limit=1)
        if existing:
            continue
        expense_type = record.expense_category or EXPENSE_TYPE_LABELS[record.fact_type]
        Claim.create(
            {
                "name": record.document_no or record.name or expense_type,
                "source_origin": "legacy",
                "claim_type": "expense",
                "state": _map_expense_state(record),
                "project_id": record.project_id.id,
                "partner_id": record.payee_id.id or record.partner_id.id or False,
                "applicant_name": record.requester_id.name or record.handler_id.name,
                "payee": record.payee_id.display_name or record.partner_id.display_name,
                "payee_account": record.bank_account,
                "date_claim": record.business_date or record.create_date.date(),
                "expense_type": expense_type,
                "summary": record.name,
                "amount": record.amount or 0,
                "approved_amount": record.amount or 0,
                "currency_id": record.currency_id.id or env.company.currency_id.id,
                "legacy_source_model": record._name,
                "legacy_record_id": str(record.id),
                "legacy_document_no": record.document_no,
                "legacy_document_state": record.state,
                "note": record.description or record.result_note,
            }
        )
        created += 1
    return created


def _migrate_borrowing_forms(env):
    Source = env["sc.finance.expense.document"].sudo()
    Loan = env["sc.financing.loan"].sudo()
    records = Source.search([("fact_type", "=", "borrowing_form"), ("project_id", "!=", False)])
    created = 0
    for record in records:
        existing = Loan.search([("legacy_source_model", "=", record._name), ("legacy_record_id", "=", str(record.id))], limit=1)
        if existing:
            continue
        Loan.create(
            {
                "name": record.document_no or record.name or "借款单",
                "source_origin": "legacy",
                "loan_type": "borrowing_request",
                "direction": "borrowed_fund",
                "state": _map_loan_state(record),
                "project_id": record.project_id.id,
                "partner_id": record.payee_id.id or record.partner_id.id or False,
                "document_no": record.document_no,
                "document_date": record.business_date or record.create_date.date(),
                "due_date": record.repayment_due_date or record.due_date,
                "amount": record.amount or 0,
                "currency_id": record.currency_id.id or env.company.currency_id.id,
                "purpose": record.description or record.name,
                "extra_label": record.expense_category,
                "legacy_source_model": record._name,
                "legacy_record_id": str(record.id),
                "legacy_document_state": record.state,
                "legacy_counterparty_id": str(record.payee_id.id or record.partner_id.id or ""),
                "legacy_counterparty_name": record.payee_id.display_name or record.partner_id.display_name,
                "legacy_amount_field": "amount",
                "note": record.result_note,
            }
        )
        created += 1
    return created


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()
    if ICP.get_param("sc.professionalization.v17_0_0_29.done") == "1":
        return
    claim_count = _migrate_expense_claims(env)
    loan_count = _migrate_borrowing_forms(env)
    ICP.set_param("sc.professionalization.v17_0_0_29.expense_claim_count", str(claim_count))
    ICP.set_param("sc.professionalization.v17_0_0_29.borrowing_count", str(loan_count))
    ICP.set_param("sc.professionalization.v17_0_0_29.done", "1")
