# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.tools.safe_eval import safe_eval


CATEGORIES = [
    ("finance.payment.apply.pay", "smart_construction_core.action_payment_request_user_payment_apply"),
    ("finance.payment.execution.partner", "smart_construction_core.action_sc_payment_execution_partner_payment"),
    ("finance.payment.execution.company", "smart_construction_core.action_sc_payment_execution_company_finance_expense"),
    ("finance.receipt.income.project", "smart_construction_core.action_sc_receipt_income_user_income"),
    ("finance.receipt.income.progress", "smart_construction_core.action_sc_receipt_income_engineering_progress"),
    ("finance.expense.reimbursement", "smart_construction_core.action_sc_expense_claim_reimbursement_request"),
    ("finance.expense.project", "smart_construction_core.action_sc_expense_claim_project"),
    ("finance.deposit.bid.pay", "smart_construction_core.action_sc_bid_deposit_pay"),
    ("finance.deposit.bid.return", "smart_construction_core.action_sc_bid_deposit_return"),
    ("finance.deposit.contract.pay", "smart_construction_core.action_sc_contract_deposit_pay"),
    ("finance.deposit.contract.return", "smart_construction_core.action_sc_contract_deposit_return"),
    ("finance.deduction.bill", "smart_construction_core.action_sc_expense_claim_deduction_bill"),
    ("finance.deduction.paid", "smart_construction_core.action_sc_expense_claim_deduction_paid"),
    ("finance.deduction.refund", "smart_construction_core.action_sc_expense_claim_deduction_paid_refund"),
    ("finance.fund.transfer", "smart_construction_core.action_sc_fund_account_between_user"),
    ("finance.loan.borrowing", "smart_construction_core.action_sc_financing_loan_borrowing_request"),
    ("finance.loan.contractor_project_borrow", "smart_construction_core.action_sc_financing_loan_contractor_project_borrow"),
    ("finance.loan.project_borrow_company", "smart_construction_core.action_sc_financing_loan_project_borrow_company"),
    ("finance.repayment.registration", "smart_construction_core.action_sc_expense_claim_repayment_registration"),
    ("finance.repayment.contractor_project", "smart_construction_core.action_sc_expense_claim_contractor_project_repay"),
    ("finance.repayment.project_company", "smart_construction_core.action_sc_expense_claim_project_repay_company"),
]


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _parse(value, default):
    if not value:
        return default
    if isinstance(value, (dict, list, tuple)):
        return value
    return safe_eval(value)


def _project():
    return env["project.project"].sudo().create(
        {
            "name": "FBCR Project %s" % _token(),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


def _partner():
    return env["res.partner"].sudo().create({"name": "FBCR Partner %s" % _token()})


def _tax(tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "FBCR Tax %s %s" % (tax_use, _token()),
            "amount": 0.0,
            "amount_type": "percent",
            "type_tax_use": tax_use,
            "price_include": False,
            "company_id": env.company.id,
        }
    )


def _contract(project, partner, direction):
    return env["construction.contract"].sudo().create(
        {
            "subject": "FBCR Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("sale" if direction == "out" else "purchase").id,
        }
    )


def _fund_account(project, name):
    return env["sc.fund.account"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "project_id": project.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "state": "active",
        }
    )


def _context_defaults(context):
    return {
        key[len("default_") :]: value
        for key, value in (context or {}).items()
        if isinstance(key, str) and key.startswith("default_")
    }


def _base_vals(model_name, context, shared):
    vals = _context_defaults(context)
    project = shared["project"]
    partner = shared["partner"]
    contract_in = shared["contract_in"]
    contract_out = shared["contract_out"]
    currency = env.company.currency_id

    if model_name == "payment.request":
        request_type = vals.get("type") or "pay"
        vals.update(
            {
                "name": "FBCR Payment Request %s" % _token(),
                "type": request_type,
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract_out.id if request_type == "receive" else contract_in.id,
                "currency_id": currency.id,
                "amount": 101.0,
            }
        )
    elif model_name == "sc.payment.execution":
        vals.update(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract_in.id,
                "planned_amount": 102.0,
                "paid_amount": 102.0,
                "currency_id": currency.id,
                "payment_account_name": "FBCR付款户名",
                "payment_account_no": "FBCR-PAYER",
                "receipt_account_name": "FBCR收款户名",
                "receipt_account_no": "FBCR-PAYEE",
            }
        )
    elif model_name == "sc.receipt.income":
        vals.update(
            {
                "project_id": project.id,
                "partner_id": partner.id,
                "contract_id": contract_out.id,
                "amount": 103.0,
                "currency_id": currency.id,
                "receiving_account_name": "FBCR收款账户",
                "receiving_account_no": "FBCR-RECEIVE",
            }
        )
    elif model_name == "sc.expense.claim":
        claim_type = vals.get("claim_type") or "expense"
        amount = 104.0
        vals.update(
            {
                "claim_type": claim_type,
                "summary": vals.get("summary") or vals.get("expense_type") or "FBCR费用办理",
                "project_id": project.id,
                "partner_id": partner.id,
                "currency_id": currency.id,
                "amount": amount,
                "approved_amount": amount,
                "payee": "FBCR收款人",
                "receipt_account_name": "FBCR收款账户",
                "payee_account": "FBCR-PAYEE",
                "payment_account_name": "FBCR付款账户",
                "payer_account": "FBCR-PAYER",
            }
        )
    elif model_name == "sc.fund.account.operation":
        vals.update(
            {
                "operation_type": vals.get("operation_type") or "transfer_between",
                "source_account_id": shared["source_account"].id,
                "target_account_id": shared["target_account"].id,
                "project_id": project.id,
                "company_id": env.company.id,
                "currency_id": currency.id,
                "amount": 105.0,
                "operation_reason": vals.get("operation_reason") or "账户间资金往来",
            }
        )
    elif model_name == "sc.financing.loan":
        vals.update(
            {
                "loan_type": vals.get("loan_type") or "borrowing_request",
                "direction": vals.get("direction") or "borrowed_fund",
                "project_id": project.id,
                "partner_id": partner.id,
                "currency_id": currency.id,
                "amount": 106.0,
                "purpose": vals.get("purpose") or "FBCR借款申请",
            }
        )
    else:
        raise AssertionError("unsupported category model: %s" % model_name)
    return vals


def _shared_records():
    project = _project()
    partner = _partner()
    return {
        "project": project,
        "partner": partner,
        "contract_in": _contract(project, partner, "in"),
        "contract_out": _contract(project, partner, "out"),
        "source_account": _fund_account(project, "FBCR Source Account"),
        "target_account": _fund_account(project, "FBCR Target Account"),
    }


def _run_category(code, action_xmlid, shared, failures):
    action = env.ref(action_xmlid, raise_if_not_found=False)
    if not action:
        failures.append("%s: missing action %s" % (code, action_xmlid))
        return {}
    context = _parse(action.context, {})
    domain = _parse(action.domain, [])
    model_name = action.res_model
    vals = _base_vals(model_name, context, shared)
    record = env[model_name].sudo().with_context(**context).create(vals)
    domain_with_record = ["&", ("id", "=", record.id)] + list(domain)
    matched = env[model_name].sudo().search(domain_with_record, limit=1)
    if matched.id != record.id:
        failures.append(
            "%s: created %s/%s is not visible through action domain %s"
            % (code, model_name, record.id, action.domain)
        )
    return {
        "code": code,
        "action": action_xmlid,
        "model": model_name,
        "record_id": record.id,
        "visible": matched.id == record.id,
    }


failures = []
rows = []

try:
    shared = _shared_records()
    for code, action_xmlid in CATEGORIES:
        with env.cr.savepoint():
            rows.append(_run_category(code, action_xmlid, shared, failures))
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_business_category_runtime_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(CATEGORIES),
    "rows": rows,
    "failures": failures,
}
print("FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
