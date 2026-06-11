# -*- coding: utf-8 -*-
"""Audit expense/deposit/deduction/repayment approval policy closure."""

from __future__ import annotations

import base64
import json
import sys
import traceback

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError


EXPENSE_CATEGORY_CODES = [
    "finance.expense.reimbursement",
    "finance.expense.project",
    "finance.deposit.bid.pay",
    "finance.deposit.bid.return",
    "finance.deposit.contract.pay",
    "finance.deposit.contract.return",
    "finance.deduction.bill",
    "finance.deduction.paid",
    "finance.deduction.refund",
    "finance.repayment.registration",
    "finance.repayment.contractor_project",
    "finance.repayment.project_company",
]


def _token():
    return env["ir.sequence"].sudo().next_by_code("sc.business.fact") or str(fields.Datetime.now())  # noqa: F821


def _expect(condition, label, failures):
    if not condition:
        failures.append(label)
        return False
    return True


def _expect_exception(label, func, failures):
    try:
        with env.cr.savepoint():  # noqa: F821
            func()
    except (AccessError, UserError, ValidationError):
        return True
    except Exception as err:  # noqa: BLE001
        failures.append("%s: expected business exception, got %s: %s" % (label, type(err).__name__, err))
        return False
    failures.append("%s: expected business exception, got success" % label)
    return False


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
    env.invalidate_all()  # noqa: F821


def _set_validated(record, table):
    env.flush_all()  # noqa: F821
    env.cr.execute("UPDATE %s SET validation_status=%%s WHERE id=%%s" % table, ("validated", record.id))  # noqa: F821
    env.invalidate_all()  # noqa: F821
    record.invalidate_recordset()
    if "validation_status" in record._fields and record.validation_status != "validated":
        record.sudo().with_context(skip_validation_check=True).write({"validation_status": "validated"})
        env.flush_all()  # noqa: F821
        env.invalidate_all()  # noqa: F821
        record.invalidate_recordset()


def _project():
    return env["project.project"].sudo().create(  # noqa: F821
        {
            "name": "Finance Expense Approval Project %s" % _token(),
            "manager_id": env.user.id,  # noqa: F821
            "company_id": env.company.id,  # noqa: F821
        }
    )


def _partner():
    return env["res.partner"].sudo().create({"name": "Finance Expense Approval Partner %s" % _token()})  # noqa: F821


def _attach(record, label):
    attachment = env["ir.attachment"].sudo().create(  # noqa: F821
        {
            "name": "%s.txt" % label,
            "datas": base64.b64encode(("approval:%s" % label).encode("utf-8")).decode("ascii"),
            "res_model": record._name,
            "res_id": record.id,
            "mimetype": "text/plain",
        }
    )
    record.write({"attachment_ids": [(4, attachment.id)]})
    return attachment


def _create_repayment_claim(project, partner, label, amount=33.0):
    claim = env["sc.expense.claim"].sudo().create(  # noqa: F821
        {
            "claim_type": "project_company_repay",
            "expense_type": "还款登记",
            "project_id": project.id,
            "partner_id": partner.id,
            "amount": amount,
            "approved_amount": amount,
            "paid_amount": 0.0,
            "summary": label,
            "payment_account_name": "审批策略付款账户",
            "payer_account": "FIN-EXP-APPROVAL-PAYER-%s" % _token(),
            "receipt_account_name": "审批策略收款账户",
            "payee_account": "FIN-EXP-APPROVAL-RECEIPT-%s" % _token(),
        }
    )
    _attach(claim, label)
    return claim


def _audit_count(record, event_code):
    return env["sc.audit.log"].sudo().search_count(  # noqa: F821
        [("model", "=", record._name), ("res_id", "=", record.id), ("event_code", "=", event_code)]
    )


def _treasury_ledger(record):
    return env["sc.treasury.ledger"].sudo().search(  # noqa: F821
        [
            ("source_model", "=", record._name),
            ("source_res_id", "=", record.id),
            ("source_kind", "=", "interfund"),
            ("state", "!=", "void"),
        ],
        limit=1,
    )


def _category_policy_rows(failures, expected_policy):
    rows = []
    Category = env["sc.business.category"].sudo()  # noqa: F821
    for code in EXPENSE_CATEGORY_CODES:
        category = Category.search([("code", "=", code)], limit=1)
        if not category:
            failures.append("%s: missing business category" % code)
            continue
        rows.append(
            {
                "code": code,
                "approval_policy": category.approval_policy_id.code,
                "policy_runtime_state": category.approval_policy_id.runtime_state,
                "policy_mode": category.approval_policy_id.mode,
            }
        )
        if category.approval_policy_id != expected_policy:
            failures.append(
                "%s: expected approval_policy_id=%s, got %s"
                % (code, expected_policy.code, category.approval_policy_id.code)
            )
    return rows


failures = []
evidence = {}
policy = False
original_policy_values = {}

try:
    _ensure_groups()
    policy = env.ref("smart_construction_core.approval_policy_expense_claim", raise_if_not_found=False)  # noqa: F821
    if not policy:
        policy = env["sc.approval.policy"].sudo().search([("target_model", "=", "sc.expense.claim")], limit=1)  # noqa: F821
    policy = policy.sudo()
    _expect(bool(policy), "expense_claim_policy: expected policy", failures)
    if policy:
        original_policy_values = {
            "active": policy.active,
            "approval_required": policy.approval_required,
            "mode": policy.mode,
            "runtime_state": policy.runtime_state,
        }
        category_rows = _category_policy_rows(failures, policy)
        project = _project()
        partner = _partner()

        policy.write({"active": True, "approval_required": False, "mode": "none", "runtime_state": "tier_validation"})
        policy.sync_tier_definitions()
        optional_claim = _create_repayment_claim(project, partner, "optional approval")
        optional_claim.action_submit()
        optional_claim.invalidate_recordset()
        _expect(optional_claim.state == "approved", "optional_claim.state: expected approved after submit", failures)
        optional_claim.action_done()
        optional_claim.invalidate_recordset()
        _expect(optional_claim.state == "done", "optional_claim.state: expected done without approval", failures)
        _expect(bool(_treasury_ledger(optional_claim)), "optional_claim: expected interfund treasury ledger", failures)

        policy.write({"active": True, "approval_required": True, "mode": "single", "runtime_state": "tier_validation"})
        policy.sync_tier_definitions()
        required_claim = _create_repayment_claim(project, partner, "required approval")
        required_claim.action_submit()
        required_claim.invalidate_recordset()
        _expect(required_claim.state == "submit", "required_claim.state: expected submit before tier approval", failures)
        _expect(
            required_claim.validation_status in ("waiting", "pending", "no"),
            "required_claim.validation_status: expected approval requested",
            failures,
        )
        _expect_exception("required_claim.action_approve_before_tier", required_claim.action_approve, failures)
        _expect_exception("required_claim.action_done_before_approval", required_claim.action_done, failures)
        _set_validated(required_claim, "sc_expense_claim")
        required_claim.action_on_tier_approved()
        required_claim.invalidate_recordset()
        _expect(required_claim.state == "approved", "required_claim.state: expected approved after tier approval", failures)
        required_claim.action_done()
        required_claim.invalidate_recordset()
        _expect(required_claim.state == "done", "required_claim.state: expected done after tier approval", failures)
        _expect(bool(_treasury_ledger(required_claim)), "required_claim: expected interfund treasury ledger", failures)
        _expect(_audit_count(required_claim, "expense_claim_approved") >= 1, "required_claim: approval audit missing", failures)
        _expect(_audit_count(required_claim, "expense_claim_done") == 1, "required_claim: done audit missing", failures)

        evidence = {
            "policy_id": policy.id,
            "policy_code": policy.code,
            "category_count": len(category_rows),
            "categories": category_rows,
            "optional_claim_id": optional_claim.id,
            "optional_claim_state": optional_claim.state,
            "required_claim_id": required_claim.id,
            "required_claim_state": required_claim.state,
            "required_claim_validation_status": required_claim.validation_status,
        }
except Exception as err:  # pragma: no cover - runs inside odoo shell
    failures.append("unexpected error: %s" % err)
    failures.append(traceback.format_exc())
finally:
    if policy and original_policy_values:
        try:
            policy.write(original_policy_values)
            policy.sync_tier_definitions()
        except Exception as restore_err:  # noqa: BLE001
            failures.append("policy restore failed: %s" % restore_err)

result = {
    "audit": "finance_expense_approval_policy_audit",
    "status": "PASS" if not failures else "FAIL",
    "evidence": evidence,
    "failures": failures,
}
print("FINANCE_EXPENSE_APPROVAL_POLICY_AUDIT: %s" % json.dumps(result, ensure_ascii=False, sort_keys=True, default=str))
if failures:
    print("FAILURES:")
    for failure in failures:
        print("- %s" % failure)
sys.exit(0 if not failures else 1)
