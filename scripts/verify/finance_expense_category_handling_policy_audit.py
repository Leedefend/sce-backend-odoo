# -*- coding: utf-8 -*-
"""Audit sc.expense.claim category handling policies.

This gate keeps expense/deposit/deduction/interfund-repayment entry categories
aligned with the current handling model:

* operating cash categories require a payment/receipt request and account fields;
* interfund repayment categories explicitly do not use payment.request;
* all categories keep user-facing action bindings, attachment policy, and
  downstream fact policy.
"""

from __future__ import annotations

import base64
import json
import sys
import traceback


EXPENSE_CATEGORY_REQUIREMENTS = {
    "finance.expense.reimbursement": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger"],
        "terminal_action": "action_done",
    },
    "finance.expense.project": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger"],
        "terminal_action": "action_done",
    },
    "finance.deposit.bid.pay": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.contract.pay": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.bid.return": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deposit.contract.return": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deduction.paid": {
        "direction": "pay",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "expense_type",
            "payee",
            "receipt_account_name",
            "payee_account",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["payment.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.deduction.refund": {
        "direction": "receive",
        "payment_request_policy": "required",
        "required_fields": [
            "payment_request_id",
            "project_id",
            "partner_id",
            "amount",
            "expense_type",
            "payment_account_name",
            "payer_account",
        ],
        "ledger_facts": ["sc.treasury.ledger", "sc.finance.business.fact"],
        "terminal_action": "action_done",
    },
    "finance.repayment.registration": {
        "direction": "pay",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
    "finance.repayment.contractor_project": {
        "direction": "receive",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
    "finance.repayment.project_company": {
        "direction": "pay",
        "payment_request_policy": "not_applicable",
        "required_fields": ["project_id", "partner_id", "amount", "expense_type"],
        "ledger_facts": ["sc.interfund.movement.fact", "sc.treasury.ledger"],
        "terminal_action": "action_done",
    },
}


def _json_loads(raw, default):
    try:
        value = json.loads(raw or "")
    except (TypeError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def _source_linked_ledger_counts():
    env.cr.execute(  # noqa: F821
        """
        SELECT
            COALESCE(category.code, '<empty>') AS category_code,
            COUNT(*)::integer AS claim_count,
            COUNT(ledger.id)::integer AS source_linked_ledger_count,
            COUNT(*) FILTER (WHERE ledger.id IS NULL)::integer AS missing_ledger_count
        FROM sc_expense_claim claim
        LEFT JOIN sc_business_category category ON category.id = claim.business_category_id
        LEFT JOIN sc_treasury_ledger ledger
          ON ledger.source_model = 'sc.expense.claim'
         AND ledger.source_res_id = claim.id
         AND ledger.project_id = claim.project_id
         AND ledger.direction = CASE WHEN claim.direction = 'inflow' THEN 'in' ELSE 'out' END
         AND ledger.source_kind = CASE WHEN claim.direction = 'inflow' THEN 'legacy_receipt' ELSE 'legacy_actual_outflow' END
         AND ledger.state != 'void'
        WHERE claim.source_origin = 'legacy'
          AND claim.state = 'legacy_confirmed'
          AND claim.project_id IS NOT NULL
          AND COALESCE(claim.approved_amount, claim.amount, 0.0) > 0
        GROUP BY COALESCE(category.code, '<empty>')
        ORDER BY category_code
        """
    )
    return env.cr.dictfetchall()  # noqa: F821


def _create_attachment(record):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "finance-expense-category-policy-proof.txt",
            "datas": base64.b64encode(b"finance expense attachment policy proof").decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    record.write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _attachment_policy_runtime_check(failures):
    Project = env["project.project"].sudo()  # noqa: F821
    Partner = env["res.partner"].sudo()  # noqa: F821
    Claim = env["sc.expense.claim"].sudo()  # noqa: F821
    project = Project.create(
        {
            "name": "费用附件策略门禁项目",
            "code": "FIN-EXP-ATTACH-POLICY",
            "company_id": env.company.id,  # noqa: F821
        }
    )
    partner = Partner.create({"name": "费用附件策略门禁往来单位"})
    claim = Claim.create(
        {
            "claim_type": "project_company_repay",
            "expense_type": "还款登记",
            "project_id": project.id,
            "partner_id": partner.id,
            "amount": 18.0,
            "approved_amount": 18.0,
            "paid_amount": 0.0,
            "summary": "附件策略门禁验证",
            "payment_account_name": "附件策略付款账户",
            "payer_account": "FIN-EXP-ATTACH-PAYER",
            "receipt_account_name": "附件策略收款账户",
            "payee_account": "FIN-EXP-ATTACH-RECEIPT",
        }
    )
    runtime = {
        "category_code": claim.business_category_id.code,
        "blocked_without_attachment": False,
        "submitted_after_attachment": False,
        "record_id": claim.id,
    }
    try:
        with env.cr.savepoint():  # noqa: F821
            claim.action_submit()
    except Exception as err:  # noqa: BLE001 - Odoo shell runtime check
        if "附件" not in str(err):
            failures.append("attachment_policy_runtime: expected attachment error, got %s" % err)
        else:
            runtime["blocked_without_attachment"] = True
    else:
        failures.append("attachment_policy_runtime: submit without attachment must fail")

    _create_attachment(claim)
    claim.action_submit()
    if claim.state not in ("submit", "approved"):
        failures.append("attachment_policy_runtime: expected submit/approved after attachment, got %s" % claim.state)
    else:
        runtime["submitted_after_attachment"] = True
        runtime["state_after_attachment"] = claim.state
    return runtime


failures = []
rows = []
ledger_counts = []
attachment_policy_runtime = {}

try:
    Category = env["sc.business.category"].sudo()  # noqa: F821
    for code, expected in EXPENSE_CATEGORY_REQUIREMENTS.items():
        category = Category.search([("code", "=", code)], limit=1)
        if not category:
            failures.append("%s: missing business category" % code)
            continue
        required_fields = _json_loads(category.required_fields_json, [])
        ledger_policy = _json_loads(category.ledger_policy_json, {})
        facts = ledger_policy.get("facts") if isinstance(ledger_policy.get("facts"), list) else []
        missing_required = [field for field in expected["required_fields"] if field not in required_fields]
        missing_facts = [fact for fact in expected["ledger_facts"] if fact not in facts]
        if not category.active:
            failures.append("%s: category inactive" % code)
        if category.target_model != "sc.expense.claim":
            failures.append("%s: expected target_model=sc.expense.claim, got %s" % (code, category.target_model))
        if category.direction != expected["direction"]:
            failures.append("%s: expected direction=%s, got %s" % (code, expected["direction"], category.direction))
        if not category.action_xmlid:
            failures.append("%s: missing action_xmlid" % code)
        elif not env.ref(category.action_xmlid, raise_if_not_found=False):  # noqa: F821
            failures.append("%s: action_xmlid not found: %s" % (code, category.action_xmlid))
        if category.attachment_policy != "required":
            failures.append("%s: attachment_policy must be required, got %s" % (code, category.attachment_policy))
        if missing_required:
            failures.append("%s: missing required_fields %s" % (code, ",".join(missing_required)))
        if missing_facts:
            failures.append("%s: missing ledger_policy facts %s" % (code, ",".join(missing_facts)))
        if ledger_policy.get("terminal_action") != expected["terminal_action"]:
            failures.append(
                "%s: expected terminal_action=%s, got %s"
                % (code, expected["terminal_action"], ledger_policy.get("terminal_action"))
            )
        actual_payment_policy = ledger_policy.get("payment_request_policy")
        if expected["payment_request_policy"] == "not_applicable":
            if actual_payment_policy != "not_applicable":
                failures.append("%s: expected payment_request_policy=not_applicable" % code)
            if "payment_request_id" in required_fields:
                failures.append("%s: interfund repayment category must not require payment_request_id" % code)
            if "payment.ledger" in facts:
                failures.append("%s: interfund repayment category must not write payment.ledger" % code)
        elif "payment_request_id" not in required_fields:
            failures.append("%s: operating cash category must require payment_request_id" % code)
        rows.append(
            {
                "code": code,
                "direction": category.direction,
                "action_xmlid": category.action_xmlid,
                "required_fields": required_fields,
                "attachment_policy": category.attachment_policy,
                "ledger_policy": ledger_policy,
                "missing_required": missing_required,
                "missing_facts": missing_facts,
            }
        )
    ledger_counts = _source_linked_ledger_counts()
    for row in ledger_counts:
        if row["category_code"] in EXPENSE_CATEGORY_REQUIREMENTS and row["missing_ledger_count"]:
            failures.append(
                "%s: %s legacy expense claims missing source-linked treasury ledger"
                % (row["category_code"], row["missing_ledger_count"])
            )
    attachment_policy_runtime = _attachment_policy_runtime_check(failures)
except Exception as err:
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())

result = {
    "audit": "finance_expense_category_handling_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "category_count": len(EXPENSE_CATEGORY_REQUIREMENTS),
    "rows": rows,
    "legacy_source_linked_ledger_counts": ledger_counts,
    "attachment_policy_runtime": attachment_policy_runtime,
    "failures": failures,
    "policy": {
        "operating_cash": "requires payment_request_id and account fields",
        "interfund_repayment": "must keep payment_request_id out of required fields and ledger policy",
        "legacy_cashflow": "legacy confirmed expense claims must have sc.treasury.ledger source_model/source_res_id coverage",
    },
}
print("FINANCE_EXPENSE_CATEGORY_HANDLING_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)

sys.exit(0 if not failures else 1)
