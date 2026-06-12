# -*- coding: utf-8 -*-
"""Audit account/interfund handling closure.

Run inside Odoo shell:
    DB_NAME=sc_demo bash scripts/ops/validate_interfund_account_loan_closure.sh
"""

from __future__ import annotations

import ast
import base64
import json

from odoo import fields
from odoo.osv import expression


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _parse(value, default):
    if not value:
        return default
    if isinstance(value, (dict, list, tuple)):
        return value
    return ast.literal_eval(value)


def _assert(errors, key, condition, details=None):
    if not condition:
        errors.append({"key": key, "details": details or {}})


def _assert_amount(errors, key, expected, actual, tolerance=0.01):
    if abs(float(expected or 0.0) - float(actual or 0.0)) > tolerance:
        errors.append({"key": key, "expected": expected, "actual": actual})


def _project(name):
    project = env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
            "funding_enabled": True,
        }
    )
    env["project.funding.baseline"].sudo().create(  # noqa: F821
        {
            "project_id": project.id,
            "total_amount": 100000.0,
            "state": "active",
        }
    )
    return project


def _partner():
    return env["res.partner"].sudo().create({"name": "Interfund Partner %s" % _token()})  # noqa: F821


def _fund_account(project, name):
    return env["sc.fund.account"].sudo().create(  # noqa: F821
        {
            "name": "%s %s" % (name, _token()),
            "project_id": project.id,
            "company_id": env.company.id,  # noqa: F821
            "currency_id": _cny().id,
            "state": "active",
        }
    )


def _cny():
    currency = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
    _assert(errors, "missing_base_cny", bool(currency))
    return currency or env.company.currency_id  # noqa: F821


def _action(action_xmlid):
    action = env.ref(action_xmlid, raise_if_not_found=False)  # noqa: F821
    _assert(errors, "missing_action_%s" % action_xmlid, bool(action))
    return action


def _visible(action, record):
    domain = _parse(action.domain, [])
    domain_with_record = expression.AND([[("id", "=", record.id)], list(domain)])
    return env[action.res_model].sudo().search(domain_with_record, limit=1).id == record.id  # noqa: F821


def _audit_count(model, res_id, event_code):
    return env["sc.audit.log"].sudo().search_count(  # noqa: F821
        [("model", "=", model), ("res_id", "=", res_id), ("event_code", "=", event_code)]
    )


def _fact(source_model, source_res_id):
    return env["sc.interfund.movement.fact"].sudo().search(  # noqa: F821
        [("source_model", "=", source_model), ("source_res_id", "=", source_res_id)],
        limit=1,
    )


def _summary(project, movement_type):
    return env["sc.interfund.movement.project.summary"].sudo().search(  # noqa: F821
        [("project_id", "=", project.id), ("movement_type", "=", movement_type)],
        limit=1,
    )


def _capital_position(project):
    return env["sc.finance.project.capital.position"].sudo().search([("project_id", "=", project.id)], limit=1)  # noqa: F821


def _cash_ledger(source, project, direction):
    return env["sc.treasury.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", source._name),
            ("source_res_id", "=", source.id),
            ("project_id", "=", project.id),
            ("direction", "=", direction),
            ("source_kind", "=", "interfund"),
        ],
        limit=1,
    )


def _ensure_groups():
    user = env.user.sudo()  # noqa: F821
    for xmlid in (
        "smart_construction_core.group_sc_cap_business_initiator",
        "smart_construction_core.group_sc_cap_finance_user",
        "smart_construction_core.group_sc_cap_finance_manager",
    ):
        group = env.ref(xmlid, raise_if_not_found=False)  # noqa: F821
        if group and group.id not in user.groups_id.ids:
            user.write({"groups_id": [(4, group.id)]})


def _attachment(record, name):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": name,
            "datas": base64.b64encode(b"interfund account loan closure evidence"),
            "res_model": record._name,
            "res_id": record.id,
            "type": "binary",
            "mimetype": "text/plain",
        }
    )
    if "attachment_ids" in record._fields:
        record.write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _approve_claim_if_needed(claim):
    claim.invalidate_recordset()
    if claim.state == "submit":
        env.cr.execute(  # noqa: F821
            "UPDATE sc_expense_claim SET validation_status=%s WHERE id=%s",
            ("validated", claim.id),
        )
        claim.invalidate_recordset()
        claim.action_on_tier_approved()
        claim.invalidate_recordset()


errors = []
evidence = {}

_ensure_groups()
cny = _cny()

source_project = _project("Interfund Source Project")
target_project = _project("Interfund Target Project")
partner = _partner()
source_account = _fund_account(source_project, "Source Account")
target_account = _fund_account(target_project, "Target Account")

fund_action = _action("smart_construction_core.action_sc_fund_account_between_user")
borrow_company_action = _action("smart_construction_core.action_sc_financing_loan_project_borrow_company")
contractor_borrow_action = _action("smart_construction_core.action_sc_financing_loan_contractor_project_borrow")

transfer_amount = 600.0
transfer = env["sc.fund.account.operation"].sudo().create(  # noqa: F821
    {
        "operation_type": "transfer_between",
        "operation_date": fields.Date.context_today(env["sc.fund.account.operation"]),  # noqa: F821
        "source_account_id": source_account.id,
        "target_account_id": target_account.id,
        "project_id": source_project.id,
        "company_id": env.company.id,  # noqa: F821
        "currency_id": cny.id,
        "amount": transfer_amount,
        "operation_reason": "账户间资金往来闭环审计",
    }
)
_assert(errors, "fund_action_visibility", _visible(fund_action, transfer))
transfer.action_confirm()
_assert(errors, "transfer_confirmed_state", transfer.state == "confirmed", {"state": transfer.state})
transfer.action_done()
_assert(errors, "transfer_done_state", transfer.state == "done", {"state": transfer.state})
_assert(errors, "transfer_confirm_audit", _audit_count(transfer._name, transfer.id, "fund_account_operation_confirmed") == 1)
_assert(errors, "transfer_done_audit", _audit_count(transfer._name, transfer.id, "fund_account_operation_done") == 1)
_assert(errors, "transfer_currency_cny", transfer.currency_id == cny, {"currency": transfer.currency_id.name})

borrow_amount = 800.0
loan = env["sc.financing.loan"].sudo().create(  # noqa: F821
    {
        "loan_type": "borrowing_request",
        "direction": "borrowed_fund",
        "project_id": target_project.id,
        "partner_id": partner.id,
        "document_date": fields.Date.context_today(env["sc.financing.loan"]),  # noqa: F821
        "currency_id": cny.id,
        "amount": borrow_amount,
        "purpose": "项目借公司款登记",
    }
)
_assert(errors, "borrow_company_action_visibility", _visible(borrow_company_action, loan))
_assert(errors, "contractor_action_excludes_company_borrow", not _visible(contractor_borrow_action, loan))
loan.action_confirm()
_assert(errors, "loan_confirmed_state", loan.state == "confirmed", {"state": loan.state})
loan.action_done()
_assert(errors, "loan_done_state", loan.state == "done", {"state": loan.state})
_assert(errors, "loan_confirm_audit", _audit_count(loan._name, loan.id, "financing_loan_confirmed") == 1)
_assert(errors, "loan_done_audit", _audit_count(loan._name, loan.id, "financing_loan_done") == 1)
_assert(errors, "loan_currency_cny", loan.currency_id == cny, {"currency": loan.currency_id.name})

contractor_borrow_amount = 300.0
contractor_loan = env["sc.financing.loan"].sudo().create(  # noqa: F821
    {
        "loan_type": "borrowing_request",
        "direction": "borrowed_fund",
        "project_id": source_project.id,
        "partner_id": partner.id,
        "document_date": fields.Date.context_today(env["sc.financing.loan"]),  # noqa: F821
        "currency_id": cny.id,
        "amount": contractor_borrow_amount,
        "purpose": "承包人借项目款",
    }
)
_assert(errors, "contractor_borrow_action_visibility", _visible(contractor_borrow_action, contractor_loan))
_assert(errors, "borrow_company_action_excludes_contractor_borrow", not _visible(borrow_company_action, contractor_loan))
contractor_loan.action_confirm()
_assert(errors, "contractor_loan_confirmed_state", contractor_loan.state == "confirmed", {"state": contractor_loan.state})
contractor_loan.action_done()
_assert(errors, "contractor_loan_done_state", contractor_loan.state == "done", {"state": contractor_loan.state})
_assert(errors, "contractor_loan_confirm_audit", _audit_count(contractor_loan._name, contractor_loan.id, "financing_loan_confirmed") == 1)
_assert(errors, "contractor_loan_done_audit", _audit_count(contractor_loan._name, contractor_loan.id, "financing_loan_done") == 1)
_assert(errors, "contractor_loan_currency_cny", contractor_loan.currency_id == cny, {"currency": contractor_loan.currency_id.name})

project_repay_company_action = _action("smart_construction_core.action_sc_expense_claim_project_repay_company")
contractor_repay_action = _action("smart_construction_core.action_sc_expense_claim_contractor_project_repay")

project_repay_amount = 200.0
project_repay = env["sc.expense.claim"].sudo().create(  # noqa: F821
    {
        "claim_type": "project_company_repay",
        "expense_type": "项目还公司款登记",
        "summary": "项目还公司款登记",
        "project_id": target_project.id,
        "partner_id": partner.id,
        "date_claim": fields.Date.context_today(env["sc.expense.claim"]),  # noqa: F821
        "currency_id": cny.id,
        "amount": project_repay_amount,
        "approved_amount": project_repay_amount,
        "payee": "Interfund Company",
        "receipt_account_name": "Interfund Company Receipt Account",
        "payee_account": "INTERFUND-COMPANY-RECEIVE",
        "payment_account_name": "Interfund Project Payment Account",
        "payer_account": "INTERFUND-PROJECT-PAY",
    }
)
_assert(errors, "project_repay_direction_outflow", project_repay.direction == "outflow", {"direction": project_repay.direction})
_assert(errors, "project_repay_action_visibility", _visible(project_repay_company_action, project_repay))
_attachment(project_repay, "interfund-project-repay-company.txt")
project_repay.action_submit()
_assert(errors, "project_repay_submit_or_approved_state", project_repay.state in ("submit", "approved"), {"state": project_repay.state})
_approve_claim_if_needed(project_repay)
_assert(errors, "project_repay_approved_state", project_repay.state == "approved", {"state": project_repay.state})
project_repay.action_done()
_assert(errors, "project_repay_done_state", project_repay.state == "done", {"state": project_repay.state})
_assert(errors, "project_repay_approved_audit", _audit_count(project_repay._name, project_repay.id, "expense_claim_approved") >= 1)
_assert(errors, "project_repay_done_audit", _audit_count(project_repay._name, project_repay.id, "expense_claim_done") == 1)
_assert(errors, "project_repay_without_payment_request", not project_repay.payment_request_id)
_assert(errors, "project_repay_currency_cny", project_repay.currency_id == cny, {"currency": project_repay.currency_id.name})

contractor_repay_amount = 120.0
contractor_repay = env["sc.expense.claim"].sudo().create(  # noqa: F821
    {
        "claim_type": "deposit_receive",
        "expense_type": "承包人还项目款",
        "summary": "承包人还项目款",
        "project_id": source_project.id,
        "partner_id": partner.id,
        "date_claim": fields.Date.context_today(env["sc.expense.claim"]),  # noqa: F821
        "currency_id": cny.id,
        "amount": contractor_repay_amount,
        "approved_amount": contractor_repay_amount,
        "payment_account_name": "Interfund Project Receipt Account",
        "payer_account": "INTERFUND-PROJECT-RECEIVE",
    }
)
_assert(errors, "contractor_repay_direction_inflow", contractor_repay.direction == "inflow", {"direction": contractor_repay.direction})
_assert(errors, "contractor_repay_action_visibility", _visible(contractor_repay_action, contractor_repay))
_attachment(contractor_repay, "interfund-contractor-repay-project.txt")
contractor_repay.action_submit()
_assert(errors, "contractor_repay_submit_or_approved_state", contractor_repay.state in ("submit", "approved"), {"state": contractor_repay.state})
_approve_claim_if_needed(contractor_repay)
_assert(errors, "contractor_repay_approved_state", contractor_repay.state == "approved", {"state": contractor_repay.state})
contractor_repay.action_done()
_assert(errors, "contractor_repay_done_state", contractor_repay.state == "done", {"state": contractor_repay.state})
_assert(errors, "contractor_repay_approved_audit", _audit_count(contractor_repay._name, contractor_repay.id, "expense_claim_approved") >= 1)
_assert(errors, "contractor_repay_done_audit", _audit_count(contractor_repay._name, contractor_repay.id, "expense_claim_done") == 1)
_assert(errors, "contractor_repay_without_payment_request", not contractor_repay.payment_request_id)
_assert(errors, "contractor_repay_currency_cny", contractor_repay.currency_id == cny, {"currency": contractor_repay.currency_id.name})

env.invalidate_all()  # noqa: F821

transfer_fact = _fact("sc.fund.account.operation", transfer.id)
_assert(errors, "transfer_fact_exists", bool(transfer_fact))
if transfer_fact:
    _assert(errors, "transfer_fact_type", transfer_fact.movement_type == "project_to_project_transfer", {"movement_type": transfer_fact.movement_type})
    _assert_amount(errors, "transfer_fact_amount", transfer_amount, transfer_fact.amount)
    _assert(errors, "transfer_fact_source_project", transfer_fact.source_project_id.id == source_project.id)
    _assert(errors, "transfer_fact_target_project", transfer_fact.target_project_id.id == target_project.id)
transfer_out_ledger = _cash_ledger(transfer, source_project, "out")
transfer_in_ledger = _cash_ledger(transfer, target_project, "in")
_assert(errors, "transfer_out_cash_ledger_exists", bool(transfer_out_ledger))
_assert(errors, "transfer_in_cash_ledger_exists", bool(transfer_in_ledger))
if transfer_out_ledger:
    _assert_amount(errors, "transfer_out_cash_ledger_amount", transfer_amount, transfer_out_ledger.amount)
    _assert(errors, "transfer_out_cash_ledger_no_request", not transfer_out_ledger.payment_request_id)
if transfer_in_ledger:
    _assert_amount(errors, "transfer_in_cash_ledger_amount", transfer_amount, transfer_in_ledger.amount)
    _assert(errors, "transfer_in_cash_ledger_no_request", not transfer_in_ledger.payment_request_id)

loan_fact = _fact("sc.financing.loan", loan.id)
_assert(errors, "loan_fact_exists", bool(loan_fact))
if loan_fact:
    _assert(errors, "loan_fact_type", loan_fact.movement_type == "company_to_project_borrow", {"movement_type": loan_fact.movement_type})
    _assert_amount(errors, "loan_fact_amount", borrow_amount, loan_fact.amount)
    _assert(errors, "loan_fact_target_project", loan_fact.target_project_id.id == target_project.id)
    _assert(errors, "loan_fact_not_contractor_borrow", loan_fact.source_project_id.id != target_project.id)
loan_cash_ledger = _cash_ledger(loan, target_project, "in")
_assert(errors, "loan_cash_ledger_exists", bool(loan_cash_ledger))
if loan_cash_ledger:
    _assert_amount(errors, "loan_cash_ledger_amount", borrow_amount, loan_cash_ledger.amount)
    _assert(errors, "loan_cash_ledger_no_request", not loan_cash_ledger.payment_request_id)

contractor_loan_fact = _fact("sc.financing.loan", contractor_loan.id)
_assert(errors, "contractor_loan_fact_exists", bool(contractor_loan_fact))
if contractor_loan_fact:
    _assert(
        errors,
        "contractor_loan_fact_type",
        contractor_loan_fact.movement_type == "project_to_contractor_borrow",
        {"movement_type": contractor_loan_fact.movement_type},
    )
    _assert_amount(errors, "contractor_loan_fact_amount", contractor_borrow_amount, contractor_loan_fact.amount)
    _assert(errors, "contractor_loan_fact_source_project", contractor_loan_fact.source_project_id.id == source_project.id)
    _assert(errors, "contractor_loan_fact_not_company_borrow", contractor_loan_fact.target_project_id.id != source_project.id)
contractor_loan_cash_ledger = _cash_ledger(contractor_loan, source_project, "out")
_assert(errors, "contractor_loan_cash_ledger_exists", bool(contractor_loan_cash_ledger))
if contractor_loan_cash_ledger:
    _assert_amount(errors, "contractor_loan_cash_ledger_amount", contractor_borrow_amount, contractor_loan_cash_ledger.amount)
    _assert(errors, "contractor_loan_cash_ledger_no_request", not contractor_loan_cash_ledger.payment_request_id)

project_repay_fact = _fact("sc.expense.claim", project_repay.id)
_assert(errors, "project_repay_fact_exists", bool(project_repay_fact))
if project_repay_fact:
    _assert(errors, "project_repay_fact_type", project_repay_fact.movement_type == "project_to_company_repay", {"movement_type": project_repay_fact.movement_type})
    _assert_amount(errors, "project_repay_fact_amount", project_repay_amount, project_repay_fact.amount)
    _assert(errors, "project_repay_fact_source_project", project_repay_fact.source_project_id.id == target_project.id)
project_repay_cash_ledger = _cash_ledger(project_repay, target_project, "out")
_assert(errors, "project_repay_cash_ledger_exists", bool(project_repay_cash_ledger))
if project_repay_cash_ledger:
    _assert_amount(errors, "project_repay_cash_ledger_amount", project_repay_amount, project_repay_cash_ledger.amount)
    _assert(errors, "project_repay_cash_ledger_no_request", not project_repay_cash_ledger.payment_request_id)

contractor_repay_fact = _fact("sc.expense.claim", contractor_repay.id)
_assert(errors, "contractor_repay_fact_exists", bool(contractor_repay_fact))
if contractor_repay_fact:
    _assert(errors, "contractor_repay_fact_type", contractor_repay_fact.movement_type == "contractor_to_project_repay", {"movement_type": contractor_repay_fact.movement_type})
    _assert_amount(errors, "contractor_repay_fact_amount", contractor_repay_amount, contractor_repay_fact.amount)
    _assert(errors, "contractor_repay_fact_target_project", contractor_repay_fact.target_project_id.id == source_project.id)
contractor_repay_cash_ledger = _cash_ledger(contractor_repay, source_project, "in")
_assert(errors, "contractor_repay_cash_ledger_exists", bool(contractor_repay_cash_ledger))
if contractor_repay_cash_ledger:
    _assert_amount(errors, "contractor_repay_cash_ledger_amount", contractor_repay_amount, contractor_repay_cash_ledger.amount)
    _assert(errors, "contractor_repay_cash_ledger_no_request", not contractor_repay_cash_ledger.payment_request_id)

source_transfer_summary = _summary(source_project, "project_to_project_transfer")
target_transfer_summary = _summary(target_project, "project_to_project_transfer")
target_borrow_summary = _summary(target_project, "company_to_project_borrow")
source_contractor_borrow_summary = _summary(source_project, "project_to_contractor_borrow")
target_project_repay_summary = _summary(target_project, "project_to_company_repay")
source_contractor_repay_summary = _summary(source_project, "contractor_to_project_repay")
_assert(errors, "source_transfer_summary_exists", bool(source_transfer_summary))
_assert(errors, "target_transfer_summary_exists", bool(target_transfer_summary))
_assert(errors, "target_borrow_summary_exists", bool(target_borrow_summary))
_assert(errors, "source_contractor_borrow_summary_exists", bool(source_contractor_borrow_summary))
_assert(errors, "target_project_repay_summary_exists", bool(target_project_repay_summary))
_assert(errors, "source_contractor_repay_summary_exists", bool(source_contractor_repay_summary))
if source_transfer_summary:
    _assert_amount(errors, "source_transfer_summary_outflow", transfer_amount, source_transfer_summary.outflow_amount)
    _assert_amount(errors, "source_transfer_summary_net", -transfer_amount, source_transfer_summary.net_amount)
if target_transfer_summary:
    _assert_amount(errors, "target_transfer_summary_inflow", transfer_amount, target_transfer_summary.inflow_amount)
    _assert_amount(errors, "target_transfer_summary_net", transfer_amount, target_transfer_summary.net_amount)
if target_borrow_summary:
    _assert_amount(errors, "target_borrow_summary_inflow", borrow_amount, target_borrow_summary.inflow_amount)
    _assert_amount(errors, "target_borrow_summary_net", borrow_amount, target_borrow_summary.net_amount)
if source_contractor_borrow_summary:
    _assert_amount(errors, "source_contractor_borrow_summary_outflow", contractor_borrow_amount, source_contractor_borrow_summary.outflow_amount)
    _assert_amount(errors, "source_contractor_borrow_summary_net", -contractor_borrow_amount, source_contractor_borrow_summary.net_amount)
if target_project_repay_summary:
    _assert_amount(errors, "target_project_repay_summary_outflow", project_repay_amount, target_project_repay_summary.outflow_amount)
    _assert_amount(errors, "target_project_repay_summary_net", -project_repay_amount, target_project_repay_summary.net_amount)
if source_contractor_repay_summary:
    _assert_amount(errors, "source_contractor_repay_summary_inflow", contractor_repay_amount, source_contractor_repay_summary.inflow_amount)
    _assert_amount(errors, "source_contractor_repay_summary_net", contractor_repay_amount, source_contractor_repay_summary.net_amount)

source_capital = _capital_position(source_project)
target_capital = _capital_position(target_project)
_assert(errors, "source_capital_position_exists", bool(source_capital))
_assert(errors, "target_capital_position_exists", bool(target_capital))
if source_capital:
    _assert_amount(errors, "source_capital_interfund_net", -(transfer_amount + contractor_borrow_amount) + contractor_repay_amount, source_capital.interfund_net_amount)
    _assert_amount(errors, "source_capital_transfer_out", transfer_amount, source_capital.project_transfer_out_amount)
    _assert_amount(errors, "source_capital_contractor_borrow_out", contractor_borrow_amount, source_capital.contractor_borrow_out_amount)
    _assert_amount(errors, "source_capital_contractor_repay_in", contractor_repay_amount, source_capital.contractor_repay_in_amount)
if target_capital:
    _assert_amount(errors, "target_capital_interfund_net", transfer_amount + borrow_amount - project_repay_amount, target_capital.interfund_net_amount)
    _assert_amount(errors, "target_capital_transfer_in", transfer_amount, target_capital.project_transfer_in_amount)
    _assert_amount(errors, "target_capital_company_borrow_in", borrow_amount, target_capital.company_borrow_in_amount)
    _assert_amount(errors, "target_capital_company_repay_out", project_repay_amount, target_capital.company_repay_out_amount)

evidence.update(
    {
        "currency_id": cny.id,
        "currency_name": cny.name,
        "source_project_id": source_project.id,
        "target_project_id": target_project.id,
        "source_account_id": source_account.id,
        "target_account_id": target_account.id,
        "transfer_id": transfer.id,
        "loan_id": loan.id,
        "contractor_loan_id": contractor_loan.id,
        "project_repay_id": project_repay.id,
        "contractor_repay_id": contractor_repay.id,
        "transfer_fact_id": transfer_fact.id if transfer_fact else False,
        "loan_fact_id": loan_fact.id if loan_fact else False,
        "contractor_loan_fact_id": contractor_loan_fact.id if contractor_loan_fact else False,
        "project_repay_fact_id": project_repay_fact.id if project_repay_fact else False,
        "contractor_repay_fact_id": contractor_repay_fact.id if contractor_repay_fact else False,
        "transfer_out_cash_ledger_id": transfer_out_ledger.id if transfer_out_ledger else False,
        "transfer_in_cash_ledger_id": transfer_in_ledger.id if transfer_in_ledger else False,
        "loan_cash_ledger_id": loan_cash_ledger.id if loan_cash_ledger else False,
        "contractor_loan_cash_ledger_id": contractor_loan_cash_ledger.id if contractor_loan_cash_ledger else False,
        "project_repay_cash_ledger_id": project_repay_cash_ledger.id if project_repay_cash_ledger else False,
        "contractor_repay_cash_ledger_id": contractor_repay_cash_ledger.id if contractor_repay_cash_ledger else False,
    }
)

result = {
    "audit": "interfund_account_loan_closure_audit",
    "status": "PASS" if not errors else "FAIL",
    "database": env.cr.dbname,  # noqa: F821
    "evidence": evidence,
    "errors": errors,
}
print("INTERFUND_ACCOUNT_LOAN_CLOSURE_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if errors:
    raise SystemExit(1)
