# -*- coding: utf-8 -*-
import json
import sys
import traceback

from odoo import fields
from odoo.tools.safe_eval import safe_eval


CATEGORIES = [
    ("finance.payment.apply.pay", "smart_construction_core.action_payment_request_user_payment_apply"),
    ("finance.payment.apply.receive", "smart_construction_core.action_payment_request_receive"),
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
    ("finance.fund.daily_report", "smart_construction_core.action_sc_fund_daily_user_report"),
    ("finance.fund.balance_adjustment", "smart_construction_core.action_sc_fund_balance_adjustment"),
    ("finance.loan.borrowing", "smart_construction_core.action_sc_financing_loan_borrowing_request"),
    ("finance.loan.contractor_project_borrow", "smart_construction_core.action_sc_financing_loan_contractor_project_borrow"),
    ("finance.loan.project_borrow_company", "smart_construction_core.action_sc_financing_loan_project_borrow_company"),
    ("finance.self_funding.income", "smart_construction_core.action_sc_self_funding_registration_income"),
    ("finance.self_funding.refund", "smart_construction_core.action_sc_self_funding_registration_refund"),
    ("finance.repayment.registration", "smart_construction_core.action_sc_expense_claim_repayment_registration"),
    ("finance.repayment.contractor_project", "smart_construction_core.action_sc_expense_claim_contractor_project_repay"),
    ("finance.repayment.project_company", "smart_construction_core.action_sc_expense_claim_project_repay_company"),
]
READONLY_CATEGORIES = [
    (
        "finance.responsibility.arrival_confirmation",
        "arrival_confirmation",
        "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    ),
    (
        "finance.responsibility.self_funding_income",
        "self_funding_income",
        "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    ),
    (
        "finance.responsibility.self_funding_refund",
        "self_funding_refund",
        "smart_construction_core.action_sc_company_contractor_responsibility_fact",
    ),
    (
        "finance.responsibility.company_contractor.balance",
        None,
        "smart_construction_core.action_sc_company_contractor_responsibility_summary",
    ),
]


def _expense_claim_category_bindings():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT claim.id,
                   CASE
                       WHEN claim.claim_type = 'deposit_pay' AND claim.guarantee_type = 'contract'
                           THEN 'finance.deposit.contract.pay'
                       WHEN claim.claim_type = 'deposit_pay'
                           THEN 'finance.deposit.bid.pay'
                       WHEN claim.claim_type = 'deposit_refund' AND claim.guarantee_type = 'contract'
                           THEN 'finance.deposit.contract.return'
                       WHEN claim.claim_type = 'deposit_refund'
                           THEN 'finance.deposit.bid.return'
                       WHEN claim.claim_type = 'deduction_refund'
                             OR COALESCE(claim.expense_type, '') = '扣款实缴退回'
                           THEN 'finance.deduction.refund'
                       WHEN claim.claim_type = 'project_company_repay'
                             AND (
                                 COALESCE(claim.expense_type, '') = '项目还公司款登记'
                                 OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%项目还公司款%'
                             )
                           THEN 'finance.repayment.project_company'
                       WHEN claim.claim_type = 'project_company_repay'
                           THEN 'finance.repayment.registration'
                       WHEN claim.claim_type = 'deposit_receive'
                             AND COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%承包人还项目款%'
                           THEN 'finance.repayment.contractor_project'
                       WHEN COALESCE(claim.expense_type, '') = '扣款实缴登记'
                           THEN 'finance.deduction.paid'
                       WHEN COALESCE(claim.expense_type, '') = '扣款单'
                             OR COALESCE(claim.expense_type, '') || ' ' || COALESCE(claim.summary, '') LIKE '%扣款单%'
                           THEN 'finance.deduction.bill'
                       WHEN COALESCE(claim.expense_type, '') = '项目费用报销单'
                           THEN 'finance.expense.project'
                       ELSE 'finance.expense.reimbursement'
                   END AS expected_code,
                   category.code AS actual_code,
                   category.target_model AS actual_target_model
              FROM sc_expense_claim claim
              LEFT JOIN sc_business_category category ON category.id = claim.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count,
               SUM(CASE WHEN COALESCE(actual_target_model, '') NOT IN ('', 'sc.expense.claim') THEN 1 ELSE 0 END)::integer
                   AS target_mismatch_count
          FROM expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _receipt_income_category_bindings():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT receipt.id,
                   CASE
                       WHEN receipt.source_kind = 'receipt_income'
                            AND (
                                COALESCE(receipt.source_family, '') = 'engineering_progress_receipt_visible'
                                OR COALESCE(receipt.income_category, '') = '工程进度款收入'
                            )
                           THEN 'finance.receipt.income.progress'
                       WHEN receipt.source_kind = 'receipt_income'
                           THEN 'finance.receipt.income.project'
                       ELSE NULL
                   END AS expected_code,
                   category.code AS actual_code,
                   category.target_model AS actual_target_model
              FROM sc_receipt_income receipt
              LEFT JOIN sc_business_category category ON category.id = receipt.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count,
               SUM(CASE WHEN COALESCE(actual_target_model, '') NOT IN ('', 'sc.receipt.income') THEN 1 ELSE 0 END)::integer
                   AS target_mismatch_count
          FROM expected
         WHERE expected_code IS NOT NULL
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _payment_request_category_bindings():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT request.id,
                   CASE
                       WHEN request.type = 'receive'
                           THEN 'finance.payment.apply.receive'
                       ELSE 'finance.payment.apply.pay'
                   END AS expected_code,
                   category.code AS actual_code,
                   category.target_model AS actual_target_model
              FROM payment_request request
              LEFT JOIN sc_business_category category ON category.id = request.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count,
               SUM(CASE WHEN COALESCE(actual_target_model, '') NOT IN ('', 'payment.request') THEN 1 ELSE 0 END)::integer
                   AS target_mismatch_count
          FROM expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _payment_execution_category_bindings():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT execution.id,
                   CASE
                       WHEN COALESCE(execution.payment_family, '') IN ('公司财务支出', 'actual_outflow')
                           THEN 'finance.payment.execution.company'
                       ELSE 'finance.payment.execution.partner'
                   END AS expected_code,
                   category.code AS actual_code,
                   category.target_model AS actual_target_model
              FROM sc_payment_execution execution
              LEFT JOIN sc_business_category category ON category.id = execution.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count,
               SUM(CASE WHEN COALESCE(actual_target_model, '') NOT IN ('', 'sc.payment.execution') THEN 1 ELSE 0 END)::integer
                   AS target_mismatch_count
          FROM expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _fund_account_operation_category_bindings():
    env.cr.execute(  # noqa: F821
        """
        WITH expected AS (
            SELECT operation.id,
                   CASE
                       WHEN operation.operation_type = 'fund_daily_report'
                           THEN 'finance.fund.daily_report'
                       WHEN operation.operation_type = 'balance_adjustment'
                           THEN 'finance.fund.balance_adjustment'
                       ELSE 'finance.fund.transfer'
                   END AS expected_code,
                   category.code AS actual_code,
                   category.target_model AS actual_target_model
              FROM sc_fund_account_operation operation
              LEFT JOIN sc_business_category category ON category.id = operation.business_category_id
        )
        SELECT expected_code,
               COUNT(*)::integer AS row_count,
               SUM(CASE WHEN actual_code = expected_code THEN 1 ELSE 0 END)::integer AS matched_count,
               SUM(CASE WHEN COALESCE(actual_code, '') != expected_code THEN 1 ELSE 0 END)::integer AS mismatch_count,
               SUM(CASE WHEN COALESCE(actual_target_model, '') NOT IN ('', 'sc.fund.account.operation') THEN 1 ELSE 0 END)::integer
                   AS target_mismatch_count
          FROM expected
         GROUP BY expected_code
         ORDER BY expected_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


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
    vals = {
        key: value
        for key, value in _context_defaults(context).items()
        if key in env[model_name]._fields  # noqa: F821
    }
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
        operation_type = vals.get("operation_type") or "transfer_between"
        vals.update(
            {
                "operation_type": operation_type,
                "source_account_id": shared["source_account"].id,
                "target_account_id": shared["target_account"].id,
                "project_id": project.id,
                "company_id": env.company.id,
                "currency_id": currency.id,
                "amount": 105.0,
                "operation_reason": vals.get("operation_reason") or "账户资金办理",
            }
        )
        if operation_type == "fund_daily_report":
            vals.update(
                {
                    "source_account_id": False,
                    "target_account_id": False,
                    "fund_account_id": shared["source_account"].id,
                    "daily_income": 105.0,
                    "daily_expense": 35.0,
                    "account_balance": 1005.0,
                    "bank_balance": 1005.0,
                    "operation_reason": vals.get("operation_reason") or "资金日报表",
                }
            )
        elif operation_type == "balance_adjustment":
            vals.update(
                {
                    "source_account_id": False,
                    "target_account_id": False,
                    "fund_account_id": shared["source_account"].id,
                    "before_balance": 1000.0,
                    "after_balance": 1005.0,
                    "operation_reason": vals.get("operation_reason") or "余额调整",
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
    elif model_name == "sc.self.funding.registration":
        vals.update(
            {
                "funding_type": vals.get("funding_type") or "income",
                "project_id": project.id,
                "partner_id": partner.id,
                "company_id": env.company.id,
                "currency_id": currency.id,
                "amount": 107.0,
                "summary": vals.get("summary") or "FBCR自筹办理",
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
    if "business_category_id" in record._fields:
        actual_code = record.business_category_id.code
        if actual_code != code:
            failures.append(
                "%s: expected business_category_id.code=%s, got %s"
                % (code, code, actual_code or "-")
            )
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
        "business_category": record.business_category_id.code if "business_category_id" in record._fields else False,
        "visible": matched.id == record.id,
    }


def _run_readonly_category(code, expected_responsibility_type, action_xmlid, failures):
    category = env["sc.business.category"].sudo().search([("code", "=", code)], limit=1)
    if not category:
        failures.append("%s: missing business category" % code)
        return {}
    if category.action_xmlid != action_xmlid:
        failures.append("%s: expected action %s, got %s" % (code, action_xmlid, category.action_xmlid))
    action = category.action_open_bound_entry()
    model_name = action.get("res_model")
    domain = action.get("domain") or []
    if model_name != category.target_model:
        failures.append("%s: bound action model expected %s, got %s" % (code, category.target_model, model_name))
    count = env[model_name].sudo().search_count(domain)
    if count <= 0:
        failures.append("%s: expected readonly category domain to match rows, got 0 for %s" % (code, domain))
    if expected_responsibility_type:
        wrong_count = env[model_name].sudo().search_count(
            ["&"] + list(domain) + [("responsibility_type", "!=", expected_responsibility_type)]
        )
        if wrong_count:
            failures.append(
                "%s: category domain leaked %s rows outside responsibility_type=%s"
                % (code, wrong_count, expected_responsibility_type)
            )
    return {
        "code": code,
        "action": action_xmlid,
        "model": model_name,
        "domain": domain,
        "matched_count": count,
        "responsibility_type": expected_responsibility_type,
    }


failures = []
rows = []

try:
    shared = _shared_records()
    for code, action_xmlid in CATEGORIES:
        with env.cr.savepoint():
            rows.append(_run_category(code, action_xmlid, shared, failures))
    for code, expected_responsibility_type, action_xmlid in READONLY_CATEGORIES:
        rows.append(_run_readonly_category(code, expected_responsibility_type, action_xmlid, failures))
    expense_claim_bindings = _expense_claim_category_bindings()
    for row in expense_claim_bindings:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched expense claim category rows of %s"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
        if row["target_mismatch_count"]:
            failures.append(
                "%s: %s expense claim rows bound to non-expense target model"
                % (row["expected_code"], row["target_mismatch_count"])
            )
    receipt_income_bindings = _receipt_income_category_bindings()
    for row in receipt_income_bindings:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched receipt income category rows of %s"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
        if row["target_mismatch_count"]:
            failures.append(
                "%s: %s receipt income rows bound to non-receipt target model"
                % (row["expected_code"], row["target_mismatch_count"])
            )
    payment_request_bindings = _payment_request_category_bindings()
    for row in payment_request_bindings:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched payment request category rows of %s"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
        if row["target_mismatch_count"]:
            failures.append(
                "%s: %s payment request rows bound to non-payment-request target model"
                % (row["expected_code"], row["target_mismatch_count"])
            )
    payment_execution_bindings = _payment_execution_category_bindings()
    for row in payment_execution_bindings:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched payment execution category rows of %s"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
        if row["target_mismatch_count"]:
            failures.append(
                "%s: %s payment execution rows bound to non-payment-execution target model"
                % (row["expected_code"], row["target_mismatch_count"])
            )
    fund_account_operation_bindings = _fund_account_operation_category_bindings()
    for row in fund_account_operation_bindings:
        if row["mismatch_count"]:
            failures.append(
                "%s: %s mismatched fund account operation category rows of %s"
                % (row["expected_code"], row["mismatch_count"], row["row_count"])
            )
        if row["target_mismatch_count"]:
            failures.append(
                "%s: %s fund account operation rows bound to non-fund-operation target model"
                % (row["expected_code"], row["target_mismatch_count"])
            )
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_business_category_runtime_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(CATEGORIES) + len(READONLY_CATEGORIES),
    "rows": rows,
    "expense_claim_bindings": expense_claim_bindings if "expense_claim_bindings" in locals() else [],
    "receipt_income_bindings": receipt_income_bindings if "receipt_income_bindings" in locals() else [],
    "payment_request_bindings": payment_request_bindings if "payment_request_bindings" in locals() else [],
    "payment_execution_bindings": payment_execution_bindings if "payment_execution_bindings" in locals() else [],
    "fund_account_operation_bindings": fund_account_operation_bindings if "fund_account_operation_bindings" in locals() else [],
    "failures": failures,
}
print("FINANCE_BUSINESS_CATEGORY_RUNTIME_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
