# -*- coding: utf-8 -*-
"""Audit interfund handling category policies.

Internal fund movement categories must stay separate from operating
payment/receipt requests. This gate checks the dictionary policies, entry
bindings, source facts, and high-confidence classification coverage for the
company/project/contractor fund responsibility flow.
"""

from __future__ import annotations

import json
import sys
import traceback

from odoo.exceptions import UserError


INTERFUND_CATEGORY_REQUIREMENTS = {
    "finance.fund.transfer": {
        "target_model": "sc.fund.account.operation",
        "direction": "transfer",
        "required_fields": ["operation_date", "amount", "source_account_id", "target_account_id"],
        "movement_types": [
            "project_to_project_transfer",
            "same_project_account_transfer",
            "project_to_company_transfer",
            "company_to_project_transfer",
            "unclassified_account_transfer",
        ],
    },
    "finance.loan.borrowing": {
        "target_model": "sc.financing.loan",
        "direction": "receive",
        "required_fields": ["project_id", "partner_id", "document_date", "amount"],
        "movement_types": [],
    },
    "finance.loan.contractor_project_borrow": {
        "target_model": "sc.financing.loan",
        "direction": "pay",
        "required_fields": ["project_id", "partner_id", "document_date", "amount"],
        "movement_types": ["project_to_contractor_borrow"],
    },
    "finance.loan.project_borrow_company": {
        "target_model": "sc.financing.loan",
        "direction": "receive",
        "required_fields": ["project_id", "partner_id", "document_date", "amount"],
        "movement_types": ["company_to_project_borrow"],
    },
    "finance.repayment.registration": {
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "movement_types": [],
    },
    "finance.repayment.contractor_project": {
        "target_model": "sc.expense.claim",
        "direction": "receive",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "movement_types": ["contractor_to_project_repay"],
    },
    "finance.repayment.project_company": {
        "target_model": "sc.expense.claim",
        "direction": "pay",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "movement_types": ["project_to_company_repay"],
    },
}


def _json_loads(raw, default):
    try:
        value = json.loads(raw or "")
    except (TypeError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def _dictfetchall(query, params=None):
    env.cr.execute(query, params or [])  # noqa: F821
    return env.cr.dictfetchall()  # noqa: F821


def _fact_counts():
    return _dictfetchall(
        """
        SELECT movement_type,
               source_model,
               COUNT(*)::integer AS fact_count,
               COUNT(*) FILTER (WHERE classification_confidence = 'high')::integer AS high_confidence_count,
               COUNT(*) FILTER (WHERE classification_confidence <> 'high')::integer AS non_high_confidence_count,
               COALESCE(SUM(amount), 0.0) AS amount
          FROM sc_interfund_movement_fact
         GROUP BY movement_type, source_model
         ORDER BY movement_type, source_model
        """
    )


def _loan_category_counts():
    return _dictfetchall(
        """
        SELECT COALESCE(category.code, '<missing>') AS category_code,
               COUNT(*)::integer AS record_count,
               COUNT(fact.id)::integer AS fact_count,
               COUNT(*) FILTER (WHERE fact.classification_confidence = 'high')::integer AS high_confidence_count,
               COUNT(*) FILTER (WHERE fact.id IS NULL)::integer AS missing_fact_count
          FROM sc_financing_loan loan
          LEFT JOIN sc_business_category category ON category.id = loan.business_category_id
          LEFT JOIN sc_interfund_movement_fact fact
            ON fact.source_model = 'sc.financing.loan'
           AND fact.source_res_id = loan.id
         WHERE loan.active IS TRUE
           AND loan.loan_type = 'borrowing_request'
           AND loan.direction = 'borrowed_fund'
         GROUP BY COALESCE(category.code, '<missing>')
         ORDER BY category_code
        """
    )


def _repayment_category_counts():
    return _dictfetchall(
        """
        SELECT COALESCE(category.code, '<missing>') AS category_code,
               COUNT(*)::integer AS record_count,
               COUNT(fact.id)::integer AS fact_count,
               COUNT(*) FILTER (WHERE fact.classification_confidence = 'high')::integer AS high_confidence_count,
               COUNT(*) FILTER (WHERE fact.id IS NULL)::integer AS missing_fact_count
          FROM sc_expense_claim claim
          LEFT JOIN sc_business_category category ON category.id = claim.business_category_id
          LEFT JOIN sc_interfund_movement_fact fact
            ON fact.source_model = 'sc.expense.claim'
           AND fact.source_res_id = claim.id
         WHERE claim.active IS TRUE
           AND (
                claim.claim_type = 'project_company_repay'
             OR (
                    claim.expense_type = '承包人还项目款'
                AND claim.claim_type IN ('expense', 'deposit_receive')
                )
           )
         GROUP BY COALESCE(category.code, '<missing>')
         ORDER BY category_code
        """
    )


def _source_linked_treasury_counts():
    return _dictfetchall(
        """
        SELECT fact.movement_type,
               fact.source_model,
               COUNT(*)::integer AS fact_count,
               COUNT(ledger.id)::integer AS source_linked_ledger_count,
               COUNT(*) FILTER (WHERE ledger.id IS NULL)::integer AS missing_ledger_count
          FROM sc_interfund_movement_fact fact
          LEFT JOIN sc_treasury_ledger ledger
            ON ledger.source_model = fact.source_model
           AND ledger.source_res_id = fact.source_res_id
           AND ledger.project_id = fact.project_id
           AND ledger.source_kind = 'interfund'
           AND ledger.state != 'void'
           AND ledger.direction = CASE WHEN fact.direction = 'in' THEN 'in' ELSE 'out' END
         WHERE fact.source_model IN ('sc.financing.loan', 'sc.expense.claim')
           AND COALESCE(fact.amount, 0.0) > 0
           AND fact.movement_type IN (
                'company_to_project_borrow',
                'project_to_company_repay',
                'project_to_contractor_borrow',
                'contractor_to_project_repay'
           )
         GROUP BY fact.movement_type, fact.source_model
         ORDER BY fact.movement_type, fact.source_model
        """
    )


def _domain_contains_category(category, code):
    return "business_category_id.code" in (category.domain_json or "") and code in (category.domain_json or "")


def _assert_borrowing_done_guard(failures):
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    Category = env["sc.business.category"].sudo()  # noqa: F821
    Loan = env["sc.financing.loan"].sudo()  # noqa: F821
    project = Project.search([], limit=1)
    partner = Partner.search([], limit=1)
    generic = Category.search([("code", "=", "finance.loan.borrowing")], limit=1)
    contractor_project = Category.search([("code", "=", "finance.loan.contractor_project_borrow")], limit=1)
    project_company = Category.search([("code", "=", "finance.loan.project_borrow_company")], limit=1)
    cny = env.ref("base.CNY", raise_if_not_found=False)  # noqa: F821
    if not project or not partner or not generic or not contractor_project or not project_company or not cny:
        failures.append("borrowing done guard probe missing project/partner/category/CNY fixture")
        return

    base_vals = {
        "loan_type": "borrowing_request",
        "direction": "borrowed_fund",
        "project_id": project.id,
        "partner_id": partner.id,
        "document_date": "2026-06-12",
        "amount": 100.0,
        "currency_id": cny.id,
    }
    generic_loan = Loan.new(dict(base_vals, business_category_id=generic.id))
    try:
        generic_loan._check_done_ready()
    except UserError as exc:
        if "业务分类" not in str(exc):
            failures.append("generic borrowing guard raised unexpected message: %s" % exc)
    else:
        failures.append("generic finance.loan.borrowing can pass done readiness without specific interfund category")

    for category in (contractor_project, project_company):
        specific = Loan.new(dict(base_vals, business_category_id=category.id))
        try:
            specific._check_done_ready()
        except UserError as exc:
            failures.append("%s should pass borrowing done readiness, got %s" % (category.code, exc))


failures = []
warnings = []
rows = []

try:
    Category = env["sc.business.category"].sudo()  # noqa: F821
    for code, expected in INTERFUND_CATEGORY_REQUIREMENTS.items():
        category = Category.search([("code", "=", code)], limit=1)
        if not category:
            failures.append("%s: missing business category" % code)
            continue
        required_fields = _json_loads(category.required_fields_json, [])
        ledger_policy = _json_loads(category.ledger_policy_json, {})
        facts = ledger_policy.get("facts") if isinstance(ledger_policy.get("facts"), list) else []
        missing_required = [field for field in expected["required_fields"] if field not in required_fields]
        missing_facts = [fact for fact in ("sc.interfund.movement.fact", "sc.treasury.ledger") if fact not in facts]
        if not category.active:
            failures.append("%s: category inactive" % code)
        if category.target_model != expected["target_model"]:
            failures.append("%s: expected target_model=%s, got %s" % (code, expected["target_model"], category.target_model))
        if category.direction != expected["direction"]:
            failures.append("%s: expected direction=%s, got %s" % (code, expected["direction"], category.direction))
        if not category.action_xmlid:
            failures.append("%s: missing action_xmlid" % code)
        elif not env.ref(category.action_xmlid, raise_if_not_found=False):  # noqa: F821
            failures.append("%s: action_xmlid not found: %s" % (code, category.action_xmlid))
        if missing_required:
            failures.append("%s: missing required_fields %s" % (code, ",".join(missing_required)))
        if missing_facts:
            failures.append("%s: missing ledger_policy facts %s" % (code, ",".join(missing_facts)))
        if ledger_policy.get("payment_request_policy") != "not_applicable":
            failures.append("%s: expected payment_request_policy=not_applicable" % code)
        if ledger_policy.get("terminal_action") != "action_done":
            failures.append("%s: expected terminal_action=action_done" % code)
        if "payment_request_id" in required_fields:
            failures.append("%s: internal interfund category must not require payment_request_id" % code)
        if "payment.ledger" in facts:
            failures.append("%s: internal interfund category must not write payment.ledger" % code)
        if code.startswith("finance.loan.") and code != "finance.loan.borrowing" and not _domain_contains_category(category, code):
            failures.append("%s: borrowing entry domain must be anchored by business_category_id.code" % code)
        rows.append(
            {
                "code": code,
                "target_model": category.target_model,
                "direction": category.direction,
                "required_fields": required_fields,
                "ledger_policy": ledger_policy,
                "action_xmlid": category.action_xmlid,
                "domain_json": category.domain_json,
            }
        )

    loan_counts = _loan_category_counts()
    repayment_counts = _repayment_category_counts()
    fact_counts = _fact_counts()
    treasury_counts = _source_linked_treasury_counts()

    missing_loan_categories = [row for row in loan_counts if row["category_code"] == "<missing>"]
    missing_repayment_categories = [row for row in repayment_counts if row["category_code"] == "<missing>"]
    if missing_loan_categories:
        failures.append("active borrowing records missing business_category_id: %s" % missing_loan_categories)
    if missing_repayment_categories:
        failures.append("active repayment records missing business_category_id: %s" % missing_repayment_categories)

    for row in loan_counts + repayment_counts:
        if row["missing_fact_count"]:
            failures.append("%s: missing interfund facts=%s" % (row["category_code"], row["missing_fact_count"]))
        if row["fact_count"] and row["high_confidence_count"] != row["fact_count"]:
            failures.append(
                "%s: expected all interfund facts high-confidence, got %s/%s"
                % (row["category_code"], row["high_confidence_count"], row["fact_count"])
            )

    ledger_missing_rows = [row for row in treasury_counts if row["missing_ledger_count"]]
    if ledger_missing_rows:
        failures.append("interfund facts missing source-linked treasury ledger: %s" % ledger_missing_rows)

    unclassified_transfer = [
        row for row in fact_counts if row["movement_type"] == "unclassified_account_transfer" and row["fact_count"]
    ]
    if unclassified_transfer:
        warnings.append(
            {
                "key": "unclassified_account_transfer_exists",
                "policy": "账户调拨入口可保留未完全分类记录，但交付前应按账户项目归属补齐或由用户确认归类。",
                "rows": unclassified_transfer,
            }
        )
    _assert_borrowing_done_guard(failures)

    result = {
        "db": env.cr.dbname,  # noqa: F821
        "status": "FAIL" if failures else "PASS",
        "policy": "内部往来按公司、项目、承包人三主体办理；不走经营收付款申请，不写 payment.ledger，用 sc.interfund.movement.fact 和 sc.treasury.ledger 追溯。",
        "category_count": len(rows),
        "categories": rows,
        "loan_category_counts": loan_counts,
        "repayment_category_counts": repayment_counts,
        "interfund_fact_counts": fact_counts,
        "source_linked_treasury_counts": treasury_counts,
        "warnings": warnings,
        "failures": failures,
    }
except Exception as exc:  # pragma: no cover - runs inside odoo shell
    result = {
        "db": getattr(env.cr, "dbname", "<unknown>"),  # noqa: F821
        "status": "ERROR",
        "error": str(exc),
        "traceback": traceback.format_exc(),
    }
    failures.append(str(exc))

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
if failures:
    sys.exit(1)
