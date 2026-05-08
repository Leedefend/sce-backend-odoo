#!/usr/bin/env python3
"""Validate user-facing expense fact taxonomy actions and menus in Odoo."""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade/expense_fact_taxonomy"))
OUTPUT_JSON = ARTIFACT_ROOT / "business_expense_fact_taxonomy_acceptance_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_expense_fact_taxonomy_acceptance_v1.md"


EXPECTED_ACTIONS = [
    {
        "xmlid": "smart_construction_core.action_sc_legacy_purchase_contract_fact_business",
        "model": "sc.legacy.purchase.contract.fact",
    },
    {
        "xmlid": "smart_construction_core.action_sc_payment_execution_actual_outflow",
        "model": "sc.payment.execution",
        "domain": [("source_kind", "=", "actual_outflow")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_payment_execution_outflow_request_residual",
        "model": "sc.payment.execution",
        "domain": [("source_kind", "=", "outflow_request")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_payment_residual_fact",
        "model": "sc.legacy.payment.residual.fact",
    },
    {
        "xmlid": "smart_construction_core.action_sc_expense_claim_deposit_pay",
        "model": "sc.expense.claim",
        "domain": [("claim_type", "=", "deposit_pay")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_expense_claim_deposit_refund",
        "model": "sc.expense.claim",
        "domain": [("claim_type", "=", "deposit_refund")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_expense_claim_deposit_receive",
        "model": "sc.expense.claim",
        "domain": [("claim_type", "=", "deposit_receive")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_expense_deposit_outflow_fact",
        "model": "sc.legacy.expense.deposit.fact",
        "domain": [("direction", "=", "outflow")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_expense_deposit_refund_fact",
        "model": "sc.legacy.expense.deposit.fact",
        "domain": [("direction", "=", "inflow_or_refund")],
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_expense_reimbursement_line_finance",
        "model": "sc.legacy.expense.reimbursement.line",
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_deduction_adjustment_line_finance",
        "model": "sc.legacy.deduction.adjustment.line",
    },
    {
        "xmlid": "smart_construction_core.action_sc_legacy_fund_confirmation_line_finance",
        "model": "sc.legacy.fund.confirmation.line",
    },
    {
        "xmlid": "smart_construction_core.action_sc_financing_loan_registration",
        "model": "sc.financing.loan",
        "domain": [("loan_type", "=", "loan_registration")],
    },
]


EXPECTED_MENUS = [
    {
        "xmlid": "smart_construction_core.menu_sc_expense_contract_supplier_pricing_fact",
        "parent": "smart_construction_core.menu_sc_expense_contract_group",
        "action": "smart_construction_core.action_sc_legacy_supplier_contract_pricing_fact",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_expense_contract_legacy_purchase_fact",
        "parent": "smart_construction_core.menu_sc_expense_contract_group",
        "action": "smart_construction_core.action_sc_legacy_purchase_contract_fact_business",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_payment_fact_group",
        "parent": "smart_construction_core.menu_sc_finance_center",
    },
    {
        "xmlid": "smart_construction_core.menu_payment_request",
        "parent": "smart_construction_core.menu_sc_payment_fact_group",
        "action": "smart_construction_core.action_payment_request_pay",
    },
    {
        "xmlid": "smart_construction_core.menu_payment_request_line",
        "parent": "smart_construction_core.menu_sc_payment_fact_group",
        "action": "smart_construction_core.action_payment_request_line",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_payment_execution",
        "parent": "smart_construction_core.menu_sc_payment_fact_group",
        "action": "smart_construction_core.action_sc_payment_execution_actual_outflow",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_payment_request_residual_fact",
        "parent": "smart_construction_core.menu_sc_payment_fact_group",
        "action": "smart_construction_core.action_sc_payment_execution_outflow_request_residual",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_payment_residual_fact",
        "parent": "smart_construction_core.menu_sc_payment_fact_group",
        "action": "smart_construction_core.action_sc_legacy_payment_residual_fact",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_bid_deposit_pay",
        "action": "smart_construction_core.action_sc_expense_claim_deposit_pay",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_bid_deposit_return",
        "action": "smart_construction_core.action_sc_expense_claim_deposit_refund",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_contract_deposit_register",
        "action": "smart_construction_core.action_sc_expense_claim_deposit_pay",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_contract_deposit_return",
        "action": "smart_construction_core.action_sc_expense_claim_deposit_refund",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_deposit_receive",
        "parent": "smart_construction_core.menu_sc_deposit_management_group",
        "action": "smart_construction_core.action_sc_expense_claim_deposit_receive",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_expense_deposit_outflow_fact",
        "parent": "smart_construction_core.menu_sc_expense_reimbursement_group",
        "action": "smart_construction_core.action_sc_legacy_expense_deposit_outflow_fact",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_expense_deposit_refund_fact",
        "parent": "smart_construction_core.menu_sc_expense_reimbursement_group",
        "action": "smart_construction_core.action_sc_legacy_expense_deposit_refund_fact",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_expense_reimbursement_line_finance",
        "parent": "smart_construction_core.menu_sc_expense_reimbursement_group",
        "action": "smart_construction_core.action_sc_legacy_expense_reimbursement_line_finance",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_expense_tax_adjustment_fact_group",
        "parent": "smart_construction_core.menu_sc_finance_center",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_deduction_adjustment_line_finance",
        "parent": "smart_construction_core.menu_sc_expense_tax_adjustment_fact_group",
        "action": "smart_construction_core.action_sc_legacy_deduction_adjustment_line_finance",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_tax_deduction_fact_finance",
        "parent": "smart_construction_core.menu_sc_expense_tax_adjustment_fact_group",
        "action": "smart_construction_core.action_sc_legacy_tax_deduction_fact",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_legacy_fund_confirmation_line_finance",
        "parent": "smart_construction_core.menu_sc_expense_tax_adjustment_fact_group",
        "action": "smart_construction_core.action_sc_legacy_fund_confirmation_line_finance",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_financing_loan_registration",
        "parent": "smart_construction_core.menu_sc_fund_account_group",
        "action": "smart_construction_core.action_sc_financing_loan_registration",
    },
    {
        "xmlid": "smart_construction_core.menu_sc_financing_loan",
        "parent": "smart_construction_core.menu_sc_fund_account_group",
        "action": "smart_construction_core.action_sc_financing_loan_borrowing",
    },
]


FACT_COUNTS = [
    ("expense_contracts", "construction.contract.expense", []),
    ("payment_requests", "payment.request", [("type", "=", "pay")]),
    ("payment_request_lines", "payment.request.line", []),
    ("actual_outflow_execution", "sc.payment.execution", [("source_kind", "=", "actual_outflow")]),
    ("outflow_request_residual_execution", "sc.payment.execution", [("source_kind", "=", "outflow_request")]),
    ("legacy_payment_residual", "sc.legacy.payment.residual.fact", []),
    ("expense_claims", "sc.expense.claim", [("claim_type", "=", "expense")]),
    ("deposit_pay", "sc.expense.claim", [("claim_type", "=", "deposit_pay")]),
    ("deposit_refund", "sc.expense.claim", [("claim_type", "=", "deposit_refund")]),
    ("deposit_receive", "sc.expense.claim", [("claim_type", "=", "deposit_receive")]),
    ("legacy_expense_deposit_outflow", "sc.legacy.expense.deposit.fact", [("direction", "=", "outflow")]),
    ("legacy_expense_deposit_refund", "sc.legacy.expense.deposit.fact", [("direction", "=", "inflow_or_refund")]),
    ("legacy_expense_reimbursement_lines", "sc.legacy.expense.reimbursement.line", []),
    ("legacy_deduction_adjustment_lines", "sc.legacy.deduction.adjustment.line", []),
    ("legacy_tax_deductions", "sc.legacy.tax.deduction.fact", []),
    ("legacy_fund_confirmation_lines", "sc.legacy.fund.confirmation.line", []),
    ("financing_loan_registration", "sc.financing.loan", [("loan_type", "=", "loan_registration")]),
    ("borrowing_requests", "sc.financing.loan", [("loan_type", "=", "borrowing_request")]),
    ("legacy_purchase_contracts", "sc.legacy.purchase.contract.fact", []),
    ("legacy_supplier_contract_pricing", "sc.legacy.supplier.contract.pricing.fact", []),
]


def ref(xmlid: str):
    return env.ref(xmlid, raise_if_not_found=False)  # noqa: F821


def action_domain(action) -> list:
    text = action.domain or "[]"
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError) as exc:
        raise RuntimeError({"invalid_action_domain": action.get_external_id().get(action.id), "domain": text}) from exc


def external_xmlids(records) -> list[str]:
    mapping = records.get_external_id()
    return sorted(value for value in mapping.values() if value)


errors: list[dict[str, object]] = []
actions: list[dict[str, object]] = []
menus: list[dict[str, object]] = []
counts: dict[str, int] = {}

for expected in EXPECTED_ACTIONS:
    action = ref(expected["xmlid"])
    if not action:
        errors.append({"error": "missing_action", "xmlid": expected["xmlid"]})
        continue
    actual_domain = action_domain(action)
    expected_domain = expected.get("domain")
    row = {
        "xmlid": expected["xmlid"],
        "name": action.name,
        "res_model": action.res_model,
        "domain": actual_domain,
        "groups": external_xmlids(action.groups_id),
    }
    if action.res_model != expected["model"]:
        errors.append(
            {
                "error": "action_model_mismatch",
                "xmlid": expected["xmlid"],
                "actual": action.res_model,
                "expected": expected["model"],
            }
        )
    if expected_domain is not None and actual_domain != expected_domain:
        errors.append(
            {
                "error": "action_domain_mismatch",
                "xmlid": expected["xmlid"],
                "actual": actual_domain,
                "expected": expected_domain,
            }
        )
    env[action.res_model].fields_get()  # noqa: F821
    actions.append(row)

for expected in EXPECTED_MENUS:
    menu = ref(expected["xmlid"])
    if not menu:
        errors.append({"error": "missing_menu", "xmlid": expected["xmlid"]})
        continue
    row = {
        "xmlid": expected["xmlid"],
        "name": menu.name,
        "active": menu.active,
        "parent": menu.parent_id.get_external_id().get(menu.parent_id.id) if menu.parent_id else "",
        "action": menu.action.get_external_id().get(menu.action.id) if menu.action else "",
        "groups": external_xmlids(menu.groups_id),
    }
    if not menu.active:
        errors.append({"error": "inactive_menu", "xmlid": expected["xmlid"]})
    if expected.get("parent") and row["parent"] != expected["parent"]:
        errors.append(
            {
                "error": "menu_parent_mismatch",
                "xmlid": expected["xmlid"],
                "actual": row["parent"],
                "expected": expected["parent"],
            }
        )
    if expected.get("action") and row["action"] != expected["action"]:
        errors.append(
            {
                "error": "menu_action_mismatch",
                "xmlid": expected["xmlid"],
                "actual": row["action"],
                "expected": expected["action"],
            }
        )
    menus.append(row)

for key, model, domain in FACT_COUNTS:
    counts[key] = env[model].sudo().search_count(domain)  # noqa: F821

summary = {
    "database": env.cr.dbname,  # noqa: F821
    "action_count": len(actions),
    "menu_count": len(menus),
    "db_writes": 0,
    "fact_counts": counts,
}
status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_expense_fact_taxonomy_acceptance",
    "summary": summary,
    "actions": actions,
    "menus": menus,
    "errors": errors,
    "decision": "business_expense_fact_taxonomy_ready" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUTPUT_REPORT.write_text(
    f"""# Business Expense Fact Taxonomy Acceptance v1

Status: {status}

## Summary

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## Errors

```json
{json.dumps(errors, ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
""",
    encoding="utf-8",
)

print(
    "BUSINESS_EXPENSE_FACT_TAXONOMY_ACCEPTANCE="
    + json.dumps(
        {
            "status": status,
            "action_count": len(actions),
            "menu_count": len(menus),
            "db_writes": 0,
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if errors:
    raise RuntimeError(errors)
