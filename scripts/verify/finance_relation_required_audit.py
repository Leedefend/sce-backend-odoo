# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import UserError, ValidationError


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():
            func()
    except (UserError, ValidationError):
        return True
    except Exception as err:
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


def _partner(name):
    return env["res.partner"].sudo().create({"name": "%s %s" % (name, _token())})


def _project(name):
    return env["project.project"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "manager_id": env.user.id,
            "company_id": env.company.id,
        }
    )


def _tax(name, tax_use):
    return env["account.tax"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
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
            "subject": "FRR Contract %s %s" % (direction, _token()),
            "type": direction,
            "project_id": project.id,
            "partner_id": partner.id,
            "company_id": env.company.id,
            "currency_id": env.company.currency_id.id,
            "tax_id": _tax("FRR Tax", "sale" if direction == "out" else "purchase").id,
        }
    )


def _fund_account(project, name, currency=None):
    return env["sc.fund.account"].sudo().create(
        {
            "name": "%s %s" % (name, _token()),
            "project_id": project.id if project else False,
            "company_id": env.company.id,
            "currency_id": (currency or env.company.currency_id).id,
            "state": "active",
        }
    )


def _approved_request(project, partner, contract, amount, request_type):
    request = env["payment.request"].sudo().create(
        {
            "name": "FRR Request %s" % _token(),
            "type": request_type,
            "project_id": project.id,
            "partner_id": partner.id,
            "contract_id": contract.id,
            "currency_id": env.company.currency_id.id,
            "amount": amount,
        }
    )
    env.cr.execute(
        "UPDATE payment_request SET state=%s, validation_status=%s WHERE id=%s",
        ("approved", "validated", request.id),
    )
    request.invalidate_recordset()
    return request


def _run_payment_execution_required(failures):
    project = _project("FRR Payment Execution Project")
    partner = _partner("FRR Payment Execution Partner")
    contract = _contract(project, partner, "in")
    request = _approved_request(project, partner, contract, 100.0, "pay")
    base = {
        "project_id": project.id,
        "partner_id": partner.id,
        "contract_id": contract.id,
        "planned_amount": 100.0,
        "paid_amount": 100.0,
        "payment_account_name": "FRR付款户名",
        "payment_account_no": "FRR-PAYER-001",
        "receipt_account_name": "FRR收款户名",
        "receipt_account_no": "FRR-PAYEE-001",
    }
    missing_request = env["sc.payment.execution"].sudo().create(dict(base))
    _expect_exception("payment_execution.missing_request", missing_request.action_confirm, failures)
    missing_payer = env["sc.payment.execution"].sudo().create(
        dict(base, payment_request_id=request.id, payment_account_name=False, payment_account_no=False)
    )
    _expect_exception("payment_execution.missing_payer_account", missing_payer.action_confirm, failures)
    missing_payee = env["sc.payment.execution"].sudo().create(
        dict(base, payment_request_id=request.id, receipt_account_name=False, receipt_account_no=False)
    )
    _expect_exception("payment_execution.missing_payee_account", missing_payee.action_confirm, failures)
    return {
        "missing_request": missing_request.id,
        "missing_payer_account": missing_payer.id,
        "missing_payee_account": missing_payee.id,
    }


def _run_receipt_income_required(failures):
    project = _project("FRR Receipt Project")
    partner = _partner("FRR Receipt Partner")
    contract = _contract(project, partner, "out")
    request = _approved_request(project, partner, contract, 110.0, "receive")
    base = {
        "project_id": project.id,
        "partner_id": partner.id,
        "contract_id": contract.id,
        "amount": 110.0,
        "income_category": "业务收入",
        "receiving_account_name": "FRR收款账户",
        "receiving_account_no": "FRR-RECEIVE-001",
    }
    missing_request = env["sc.receipt.income"].sudo().create(dict(base))
    _expect_exception("receipt_income.missing_request", missing_request.action_confirm, failures)
    missing_account = env["sc.receipt.income"].sudo().create(
        dict(base, payment_request_id=request.id, receiving_account_name=False, receiving_account_no=False)
    )
    _expect_exception("receipt_income.missing_receiving_account", missing_account.action_confirm, failures)
    return {"missing_request": missing_request.id, "missing_receiving_account": missing_account.id}


def _run_expense_claim_required(failures):
    project = _project("FRR Expense Project")
    partner = _partner("FRR Expense Partner")
    contract = _contract(project, partner, "in")
    request = _approved_request(project, partner, contract, 90.0, "pay")
    base = {
        "claim_type": "expense",
        "expense_type": "项目费用报销单",
        "summary": "项目费用报销单",
        "project_id": project.id,
        "partner_id": partner.id,
        "amount": 90.0,
        "approved_amount": 90.0,
        "payee": "FRR费用收款人",
        "receipt_account_name": "FRR费用收款账户",
        "payee_account": "FRR-CLAIM-PAYEE-001",
        "payment_account_name": "FRR费用付款账户",
        "payer_account": "FRR-CLAIM-PAYER-001",
    }
    missing_request = env["sc.expense.claim"].sudo().create(dict(base))
    _expect_exception("expense_claim.missing_request", missing_request.action_submit, failures)
    missing_payee = env["sc.expense.claim"].sudo().create(
        dict(base, payment_request_id=request.id, payee=False, receipt_account_name=False, payee_account=False)
    )
    _expect_exception("expense_claim.missing_payee_account", missing_payee.action_submit, failures)
    missing_payer = env["sc.expense.claim"].sudo().create(
        dict(base, payment_request_id=request.id, payment_account_name=False, payer_account=False)
    )
    _expect_exception("expense_claim.missing_payer_account", missing_payer.action_submit, failures)
    return {
        "missing_request": missing_request.id,
        "missing_payee_account": missing_payee.id,
        "missing_payer_account": missing_payer.id,
    }


def _run_fund_account_operation_required(failures):
    project = _project("FRR Fund Operation Project")
    source_account = _fund_account(project, "FRR Source Account")
    target_account = _fund_account(project, "FRR Target Account")
    base = {
        "operation_type": "transfer_between",
        "operation_date": fields.Date.context_today(env["sc.fund.account.operation"]),
        "source_account_id": source_account.id,
        "target_account_id": target_account.id,
        "project_id": project.id,
        "company_id": env.company.id,
        "currency_id": env.company.currency_id.id,
        "amount": 100.0,
        "operation_reason": "FRR账户资金关系必填审计",
    }
    _expect_exception(
        "fund_account_operation.missing_source_account",
        lambda: env["sc.fund.account.operation"].sudo().create(dict(base, source_account_id=False)),
        failures,
    )
    _expect_exception(
        "fund_account_operation.missing_target_account",
        lambda: env["sc.fund.account.operation"].sudo().create(dict(base, target_account_id=False)),
        failures,
    )
    _expect_exception(
        "fund_account_operation.same_account",
        lambda: env["sc.fund.account.operation"].sudo().create(dict(base, target_account_id=source_account.id)),
        failures,
    )
    _expect_exception(
        "fund_account_operation.non_positive_amount",
        lambda: env["sc.fund.account.operation"].sudo().create(dict(base, amount=0.0)),
        failures,
    )
    draft_transfer = env["sc.fund.account.operation"].sudo().create(dict(base))
    _expect_exception("fund_account_operation.done_from_draft", draft_transfer.action_done, failures)
    _expect_exception(
        "fund_account_operation.balance_adjustment_missing_account",
        lambda: env["sc.fund.account.operation"].sudo().create(
            {
                "operation_type": "balance_adjustment",
                "operation_date": fields.Date.context_today(env["sc.fund.account.operation"]),
                "company_id": env.company.id,
                "currency_id": env.company.currency_id.id,
                "before_balance": 10.0,
                "after_balance": 20.0,
                "operation_reason": "FRR余额调整缺账户",
            }
        ),
        failures,
    )
    _expect_exception(
        "fund_account_operation.balance_adjustment_same_balance",
        lambda: env["sc.fund.account.operation"].sudo().create(
            {
                "operation_type": "balance_adjustment",
                "operation_date": fields.Date.context_today(env["sc.fund.account.operation"]),
                "fund_account_id": source_account.id,
                "company_id": env.company.id,
                "currency_id": env.company.currency_id.id,
                "before_balance": 10.0,
                "after_balance": 10.0,
                "operation_reason": "FRR余额调整前后一致",
            }
        ),
        failures,
    )
    _expect_exception(
        "fund_account_operation.daily_report_missing_account",
        lambda: env["sc.fund.account.operation"].sudo().create(
            {
                "operation_type": "fund_daily_report",
                "operation_date": fields.Date.context_today(env["sc.fund.account.operation"]),
                "company_id": env.company.id,
                "currency_id": env.company.currency_id.id,
                "daily_income": 1.0,
                "daily_expense": 0.0,
                "account_balance": 1.0,
                "bank_balance": 1.0,
                "operation_reason": "FRR资金日报缺账户",
            }
        ),
        failures,
    )
    return {
        "draft_transfer": draft_transfer.id,
        "source_account": source_account.id,
        "target_account": target_account.id,
    }


failures = []
evidence = {}

try:
    evidence["payment_execution"] = _run_payment_execution_required(failures)
    evidence["receipt_income"] = _run_receipt_income_required(failures)
    evidence["expense_claim"] = _run_expense_claim_required(failures)
    evidence["fund_account_operation"] = _run_fund_account_operation_required(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_relation_required_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("FINANCE_RELATION_REQUIRED_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
