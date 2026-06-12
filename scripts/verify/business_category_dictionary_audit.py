# -*- coding: utf-8 -*-
import json
import sys
import traceback


EXPECTED = {
    "site.construction.diary": {
        "domain": "site",
        "target_model": "sc.construction.diary",
        "direction": "reference",
        "ledger_fact": "sc.construction.diary",
        "action_xmlid": "smart_construction_core.action_sc_construction_diary",
    },
    "site.quality.issue": {
        "domain": "site",
        "target_model": "sc.quality.issue",
        "direction": "reference",
        "ledger_fact": "sc.quality.issue",
        "action_xmlid": "smart_construction_core.action_sc_quality_issue",
    },
    "site.quality.rectification": {
        "domain": "site",
        "target_model": "sc.quality.rectification",
        "direction": "reference",
        "ledger_fact": "sc.quality.rectification",
        "action_xmlid": "smart_construction_core.action_sc_quality_rectification",
    },
    "site.quality.recheck": {
        "domain": "site",
        "target_model": "sc.quality.recheck",
        "direction": "reference",
        "ledger_fact": "sc.quality.recheck",
        "action_xmlid": "smart_construction_core.action_sc_quality_recheck",
    },
    "site.safety.issue": {
        "domain": "site",
        "target_model": "sc.safety.issue",
        "direction": "reference",
        "ledger_fact": "sc.safety.issue",
        "action_xmlid": "smart_construction_core.action_sc_safety_issue",
    },
    "site.safety.rectification": {
        "domain": "site",
        "target_model": "sc.safety.rectification",
        "direction": "reference",
        "ledger_fact": "sc.safety.rectification",
        "action_xmlid": "smart_construction_core.action_sc_safety_rectification",
    },
    "site.safety.recheck": {
        "domain": "site",
        "target_model": "sc.safety.recheck",
        "direction": "reference",
        "ledger_fact": "sc.safety.recheck",
        "action_xmlid": "smart_construction_core.action_sc_safety_recheck",
    },
    "contract.income": {
        "domain": "contract",
        "target_model": "construction.contract.income",
        "direction": "income",
        "ledger_fact": "construction.contract.income",
        "action_xmlid": "smart_construction_core.action_construction_contract_income",
    },
    "contract.expense": {
        "domain": "contract",
        "target_model": "construction.contract.expense",
        "direction": "cost",
        "ledger_fact": "construction.contract.expense",
        "action_xmlid": "smart_construction_core.action_construction_contract_expense",
    },
    "settlement.income": {
        "domain": "contract",
        "target_model": "sc.settlement.order",
        "direction": "income",
        "ledger_fact": "sc.settlement.order",
        "action_xmlid": "smart_construction_core.action_sc_settlement_order",
    },
    "settlement.expense": {
        "domain": "contract",
        "target_model": "sc.settlement.order",
        "direction": "cost",
        "ledger_fact": "sc.settlement.order",
        "action_xmlid": "smart_construction_core.action_sc_settlement_order",
    },
    "finance.payment.apply.pay": {
        "domain": "finance",
        "target_model": "payment.request",
        "direction": "pay",
        "ledger_fact": "payment.ledger",
        "action_xmlid": "smart_construction_core.action_payment_request_user_payment_apply",
    },
    "finance.payment.apply.receive": {
        "domain": "finance",
        "target_model": "payment.request",
        "direction": "receive",
        "ledger_fact": "sc.treasury.ledger",
        "action_xmlid": "smart_construction_core.action_payment_request_receive",
    },
    "finance.payment.execution.partner": {
        "domain": "finance",
        "target_model": "sc.payment.execution",
        "direction": "pay",
        "ledger_fact": "payment.ledger",
        "action_xmlid": "smart_construction_core.action_sc_payment_execution_partner_payment",
    },
    "finance.payment.execution.company": {
        "domain": "finance",
        "target_model": "sc.payment.execution",
        "direction": "pay",
        "ledger_fact": "payment.ledger",
        "action_xmlid": "smart_construction_core.action_sc_payment_execution_company_finance_expense",
    },
    "finance.receipt.income.project": {
        "domain": "finance",
        "target_model": "sc.receipt.income",
        "direction": "receive",
        "ledger_fact": "sc.treasury.ledger",
        "action_xmlid": "smart_construction_core.action_sc_receipt_income_user_income",
    },
    "finance.receipt.income.progress": {
        "domain": "finance",
        "target_model": "sc.receipt.income",
        "direction": "receive",
        "ledger_fact": "sc.treasury.ledger",
        "action_xmlid": "smart_construction_core.action_sc_receipt_income_engineering_progress",
    },
    "finance.expense.reimbursement": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "payment.ledger",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_reimbursement_request",
    },
    "finance.expense.project": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "payment.ledger",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_project",
    },
    "finance.deposit.bid.pay": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_bid_deposit_pay",
    },
    "finance.deposit.bid.return": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "receive",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_bid_deposit_return",
    },
    "finance.deposit.contract.pay": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_contract_deposit_pay",
    },
    "finance.deposit.contract.return": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "receive",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_contract_deposit_return",
    },
    "finance.deduction.bill": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "mixed",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_deduction_bill",
    },
    "finance.deduction.paid": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_deduction_paid",
    },
    "finance.deduction.refund": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "receive",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_deduction_paid_refund",
    },
    "finance.fund.transfer": {
        "domain": "finance",
        "target_model": "sc.fund.account.operation",
        "direction": "transfer",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_fund_account_between_user",
    },
    "finance.fund.daily_report": {
        "domain": "finance",
        "target_model": "sc.fund.account.operation",
        "direction": "noncash",
        "ledger_fact": "sc.treasury.ledger",
        "action_xmlid": "smart_construction_core.action_sc_fund_daily_user_report",
    },
    "finance.fund.balance_adjustment": {
        "domain": "finance",
        "target_model": "sc.fund.account.operation",
        "direction": "noncash",
        "ledger_fact": None,
        "action_xmlid": "smart_construction_core.action_sc_fund_balance_adjustment",
    },
    "finance.loan.borrowing": {
        "domain": "finance",
        "target_model": "sc.financing.loan",
        "direction": "receive",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_financing_loan_borrowing_request",
    },
    "finance.loan.contractor_project_borrow": {
        "domain": "finance",
        "target_model": "sc.financing.loan",
        "direction": "pay",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_financing_loan_contractor_project_borrow",
    },
    "finance.loan.project_borrow_company": {
        "domain": "finance",
        "target_model": "sc.financing.loan",
        "direction": "receive",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_financing_loan_project_borrow_company",
    },
    "finance.repayment.registration": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_repayment_registration",
    },
    "finance.repayment.contractor_project": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "receive",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_contractor_project_repay",
    },
    "finance.repayment.project_company": {
        "domain": "finance",
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "ledger_fact": "sc.interfund.movement.fact",
        "action_xmlid": "smart_construction_core.action_sc_expense_claim_project_repay_company",
    },
    "finance.responsibility.arrival_confirmation": {
        "domain": "finance",
        "target_model": "sc.company.contractor.responsibility.fact",
        "direction": "reference",
        "ledger_fact": "sc.company.contractor.responsibility.summary",
        "action_xmlid": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
        "ledger_expect": {
            "user_cognition": "project_receipt_status",
            "responsibility_scope": "company_contractor",
            "payment_request_policy": "not_ordinary_request",
        },
    },
    "finance.responsibility.self_funding_income": {
        "domain": "finance",
        "target_model": "sc.company.contractor.responsibility.fact",
        "direction": "reference",
        "ledger_fact": "sc.company.contractor.responsibility.summary",
        "action_xmlid": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
        "ledger_expect": {
            "user_cognition": "self_funding_business",
            "responsibility_scope": "company_contractor",
            "project_role": "attribution_and_constraint",
        },
    },
    "finance.responsibility.self_funding_refund": {
        "domain": "finance",
        "target_model": "sc.company.contractor.responsibility.fact",
        "direction": "reference",
        "ledger_fact": "sc.company.contractor.responsibility.summary",
        "action_xmlid": "smart_construction_core.action_sc_company_contractor_responsibility_fact",
        "ledger_expect": {
            "user_cognition": "self_funding_refund_business",
            "responsibility_scope": "company_contractor",
            "project_role": "attribution_and_constraint",
        },
    },
    "finance.responsibility.company_contractor.balance": {
        "domain": "finance",
        "target_model": "sc.company.contractor.responsibility.summary",
        "direction": "reference",
        "ledger_fact": "sc.company.contractor.responsibility.summary",
        "action_xmlid": "smart_construction_core.action_sc_company_contractor_responsibility_summary",
        "ledger_expect": {
            "terminal_action": "read_only_summary",
            "responsibility_scope": "company_contractor",
            "arrival_balance_policy": "separate_from_self_funding",
        },
    },
    "invoice.output.application": {
        "domain": "invoice_tax",
        "target_model": "sc.invoice.registration",
        "direction": "income",
        "ledger_fact": "sc.invoice.category.summary",
        "action_xmlid": "smart_construction_core.action_sc_invoice_application_user",
    },
    "invoice.output.registration": {
        "domain": "invoice_tax",
        "target_model": "sc.invoice.registration",
        "direction": "income",
        "ledger_fact": "sc.invoice.category.summary",
        "action_xmlid": "smart_construction_core.action_sc_invoice_registration_user",
    },
    "invoice.input.report": {
        "domain": "invoice_tax",
        "target_model": "sc.invoice.registration",
        "direction": "cost",
        "ledger_fact": "sc.invoice.category.summary",
        "action_xmlid": "smart_construction_core.action_sc_invoice_input_report_user",
    },
    "invoice.prepaid_tax": {
        "domain": "invoice_tax",
        "target_model": "sc.invoice.registration",
        "direction": "noncash_tax",
        "ledger_fact": "sc.invoice.category.summary",
        "action_xmlid": "smart_construction_core.action_sc_invoice_prepaid_tax_user",
    },
    "tax.deduction.registration": {
        "domain": "invoice_tax",
        "target_model": "sc.tax.deduction.registration",
        "direction": "noncash_tax",
        "ledger_fact": "sc.finance.business.fact",
        "action_xmlid": "smart_construction_core.action_sc_tax_deduction_registration_user",
    },
    "tax.certificate.registration": {
        "domain": "invoice_tax",
        "target_model": "sc.legacy.payment.residual.fact",
        "direction": "noncash_tax",
        "ledger_fact": "sc.legacy.payment.residual.fact",
        "action_xmlid": "smart_construction_core.action_sc_tax_certificate_registration_user",
    },
    "material.plan": {
        "domain": "material",
        "target_model": "project.material.plan",
        "direction": "cost",
        "ledger_fact": "project.material.plan",
        "action_xmlid": "smart_construction_core.action_project_material_plan_my",
    },
    "material.purchase.request": {
        "domain": "material",
        "target_model": "sc.material.purchase.request",
        "direction": "cost",
        "ledger_fact": "sc.material.purchase.request",
        "action_xmlid": "smart_construction_core.action_sc_material_purchase_request",
    },
    "material.acceptance": {
        "domain": "material",
        "target_model": "sc.material.acceptance",
        "direction": "cost",
        "ledger_fact": "sc.material.acceptance",
        "action_xmlid": "smart_construction_core.action_sc_material_acceptance",
    },
    "material.rfq": {
        "domain": "material",
        "target_model": "sc.material.rfq",
        "direction": "cost",
        "ledger_fact": "sc.material.rfq",
        "action_xmlid": "smart_construction_core.action_sc_material_rfq",
    },
    "material.inbound": {
        "domain": "material",
        "target_model": "sc.material.inbound",
        "direction": "cost",
        "ledger_fact": "sc.material.inbound",
        "action_xmlid": "smart_construction_core.action_sc_material_inbound_handling",
        "cost_triggers": {"receive_project_cost_ledger": False},
    },
    "material.outbound": {
        "domain": "material",
        "target_model": "sc.material.outbound",
        "direction": "cost",
        "ledger_fact": "sc.material.outbound",
        "action_xmlid": "smart_construction_core.action_sc_material_outbound",
        "cost_triggers": {"issue_project_cost_ledger": True},
    },
    "material.return": {
        "domain": "material",
        "target_model": "sc.material.outbound",
        "direction": "cost_reversal",
        "ledger_fact": "sc.material.outbound",
        "action_xmlid": "smart_construction_core.action_sc_material_return",
        "cost_triggers": {"issue_project_cost_ledger": False},
    },
    "material.transfer": {
        "domain": "material",
        "target_model": "sc.material.outbound",
        "direction": "transfer",
        "ledger_fact": "sc.material.outbound",
        "action_xmlid": "smart_construction_core.action_sc_material_transfer",
        "cost_triggers": {"issue_project_cost_ledger": False},
    },
    "material.loss": {
        "domain": "material",
        "target_model": "sc.material.outbound",
        "direction": "cost",
        "ledger_fact": "sc.material.outbound",
        "action_xmlid": "smart_construction_core.action_sc_material_loss",
        "cost_triggers": {"issue_project_cost_ledger": True},
    },
    "material.settlement": {
        "domain": "material",
        "target_model": "sc.material.settlement",
        "direction": "cost",
        "ledger_fact": "sc.material.settlement",
        "action_xmlid": "smart_construction_core.action_sc_material_settlement",
        "cost_triggers": {"confirm_project_cost_ledger": True, "confirm_payment_request": True},
    },
}


JSON_FIELDS = {
    "default_values_json": dict,
    "domain_json": list,
    "required_fields_json": list,
    "visible_groups_json": list,
    "ledger_policy_json": dict,
}


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _loads(record, field_name, expected_type, failures):
    try:
        value = json.loads(record[field_name] or ("[]" if expected_type is list else "{}"))
    except (TypeError, ValueError) as err:
        failures.append("%s.%s invalid json: %s" % (record.code, field_name, err))
        return None
    _expect(isinstance(value, expected_type), "%s.%s expected %s" % (record.code, field_name, expected_type.__name__), failures)
    return value


def _check_category(code, expected, failures):
    category = env["sc.business.category"].sudo().search([("code", "=", code)], limit=1)
    _expect(category, "%s missing" % code, failures)
    if not category:
        return False
    _expect(category.active, "%s expected active" % code, failures)
    _expect(category.industry_template == "construction", "%s expected construction template" % code, failures)
    _expect(category.template_key == code, "%s expected template_key=%s, got %s" % (code, code, category.template_key), failures)
    _expect(bool(category.template_version), "%s template_version missing" % code, failures)
    _expect(
        category.action_xmlid == expected["action_xmlid"],
        "%s expected action_xmlid %s, got %s" % (code, expected["action_xmlid"], category.action_xmlid),
        failures,
    )
    _expect(category.domain == expected["domain"], "%s expected domain %s, got %s" % (code, expected["domain"], category.domain), failures)
    _expect(
        category.target_model == expected["target_model"],
        "%s expected target_model %s, got %s" % (code, expected["target_model"], category.target_model),
        failures,
    )
    _expect(category.target_model in env, "%s target model not installed: %s" % (code, category.target_model), failures)
    _expect(category.direction == expected["direction"], "%s expected direction %s, got %s" % (code, expected["direction"], category.direction), failures)
    parsed = {}
    for field_name, expected_type in JSON_FIELDS.items():
        parsed[field_name] = _loads(category, field_name, expected_type, failures)
    ledger_policy = parsed.get("ledger_policy_json") or {}
    if expected["ledger_fact"]:
        _expect(
            expected["ledger_fact"] in (ledger_policy.get("facts") or []),
            "%s ledger policy missing fact %s" % (code, expected["ledger_fact"]),
            failures,
        )
    for trigger, expected_value in (expected.get("cost_triggers") or {}).items():
        triggers = ledger_policy.get("cost_triggers") or {}
        _expect(
            triggers.get(trigger) is expected_value,
            "%s expected cost trigger %s=%s, got %s" % (code, trigger, expected_value, triggers.get(trigger)),
            failures,
        )
    for key, expected_value in (expected.get("ledger_expect") or {}).items():
        _expect(
            ledger_policy.get(key) == expected_value,
            "%s expected ledger policy %s=%s, got %s" % (code, key, expected_value, ledger_policy.get(key)),
            failures,
        )
    required_fields = parsed.get("required_fields_json") or []
    _expect(bool(required_fields), "%s required fields missing" % code, failures)
    action = category.action_open_target_records()
    _expect(action.get("res_model") == category.target_model, "%s target action model mismatch" % code, failures)
    _expect(isinstance(action.get("domain"), list), "%s target action domain is not list" % code, failures)
    _expect(isinstance(action.get("context"), dict), "%s target action context is not dict" % code, failures)
    bound_action = env.ref(expected["action_xmlid"], raise_if_not_found=False)
    _expect(bound_action, "%s bound action missing: %s" % (code, expected["action_xmlid"]), failures)
    if bound_action:
        _expect(
            bound_action.res_model == category.target_model,
            "%s bound action model expected %s, got %s" % (code, category.target_model, bound_action.res_model),
            failures,
        )
        bound_result = category.action_open_bound_entry()
        _expect(bound_result.get("res_model") == category.target_model, "%s bound entry action model mismatch" % code, failures)
    return category


failures = []
rows = []

try:
    for code, expected in EXPECTED.items():
        category = _check_category(code, expected, failures)
        if category:
            rows.append(
                {
                    "code": category.code,
                    "name": category.name,
                    "domain": category.domain,
                    "target_model": category.target_model,
                    "direction": category.direction,
                    "action_xmlid": category.action_xmlid,
                }
            )
    total = env["sc.business.category"].sudo().search_count([("active", "=", True)])
    _expect(total >= len(EXPECTED), "expected at least %s active categories, got %s" % (len(EXPECTED), total), failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "business_category_dictionary_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(rows),
    "rows": rows,
    "failures": failures,
}
print("BUSINESS_CATEGORY_DICTIONARY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
