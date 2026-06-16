# -*- coding: utf-8 -*-
"""Audit whether merged handling entries cover historical business semantics.

Run with:
    docker exec -i sc-backend-odoo-dev-odoo-1 odoo shell -c /var/lib/odoo/odoo.conf -d sc_demo < scripts/verify/business_form_historical_logic_coverage_audit.py
"""

from __future__ import annotations

from collections import Counter


EXPECTED_ENTRY_CATEGORY_SETS = {
    "sc.receipt.income 收款登记": {
        "finance.receipt.income.project",
        "finance.receipt.income.progress",
        "finance.receipt.income.residual",
    },
    "sc.expense.claim 费用/扣款/保证金办理": {
        "finance.expense.reimbursement",
        "finance.expense.project",
        "finance.deduction.bill",
        "finance.deduction.paid",
        "finance.deduction.refund",
        "finance.deposit.bid.pay",
        "finance.deposit.bid.return",
        "finance.deposit.contract.pay",
        "finance.deposit.contract.return",
    },
    "sc.expense.claim 还款办理": {
        "finance.repayment.registration",
        "finance.repayment.contractor_project",
        "finance.repayment.project_company",
    },
    "sc.self.funding.registration 自筹垫付办理": {"finance.self_funding.income"},
    "sc.self.funding.registration 自筹退回办理": {"finance.self_funding.refund"},
}


HISTORICAL_MODELS = [
    "construction.contract.expense",
    "construction.contract.income",
    "sc.settlement.order",
    "sc.labor.usage",
    "sc.payment.execution",
    "payment.request",
    "sc.financing.loan",
    "sc.receipt.income",
    "sc.invoice.registration",
    "sc.self.funding.registration",
    "sc.expense.claim",
]


def _codes(value):
    return {str(item or "").strip() for item in (value or []) if str(item or "").strip()}


def _iter_menus(policy):
    for group in policy.menu_groups or []:
        for menu in (group or {}).get("menus") or []:
            if isinstance(menu, dict):
                yield menu


errors = []
summary = {}

Policy = env["sc.product.policy"].sudo()
policy = Policy.search([("product_key", "=", "construction.standard")], limit=1)
if not policy:
    errors.append("missing construction.standard product policy")
else:
    target_codes = {}
    for menu in _iter_menus(policy):
        target = str(menu.get("integration_target") or "").strip()
        if target in EXPECTED_ENTRY_CATEGORY_SETS:
            target_codes.setdefault(target, set()).update(_codes(menu.get("allowed_business_category_codes")))
    for target, expected in EXPECTED_ENTRY_CATEGORY_SETS.items():
        actual = target_codes.get(target, set())
        if actual != expected:
            errors.append("entry category mismatch %s expected=%s actual=%s" % (target, sorted(expected), sorted(actual)))
        summary[target] = sorted(actual)

Category = env["sc.business.category"].sudo()
for model in HISTORICAL_MODELS:
    if model not in env or "business_category_id" not in env[model]._fields:
        continue
    total = env[model].sudo().search_count([])
    uncategorized = env[model].sudo().search_count([("business_category_id", "=", False)])
    counts = Counter()
    for row in env[model].sudo().read_group([], ["business_category_id"], ["business_category_id"], lazy=False):
        category = row.get("business_category_id")
        code = "UNCATEGORIZED"
        if category:
            code = Category.browse(category[0]).code or str(category[0])
        counts[code] = row.get("__count", 0)
    summary[model] = {"total": total, "uncategorized": uncategorized, "categories": dict(sorted(counts.items()))}
    if total and uncategorized:
        errors.append("uncategorized historical records model=%s count=%s" % (model, uncategorized))

receipt_residual_count = env["sc.receipt.income"].sudo().search_count(
    [("business_category_id.code", "=", "finance.receipt.income.residual")]
)
summary["receipt_residual_count"] = receipt_residual_count
if receipt_residual_count < 88:
    errors.append("receipt residual coverage too low: %s" % receipt_residual_count)

if errors:
    print({"ok": False, "errors": errors, "summary": summary})
    raise AssertionError("; ".join(errors))

print({"ok": True, "summary": summary})
