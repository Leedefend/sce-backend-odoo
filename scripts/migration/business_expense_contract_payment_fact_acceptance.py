#!/usr/bin/env python3
"""Validate expense-contract payment fact materialization without inventing settlements."""

from __future__ import annotations

import json
import os
from pathlib import Path


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade/payment_fact_acceptance"))
OUTPUT_JSON = ARTIFACT_ROOT / "business_expense_contract_payment_fact_acceptance_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_expense_contract_payment_fact_acceptance_v1.md"


def scalar(sql: str, params: list[object] | None = None) -> object:
    env.cr.execute(sql, params or [])  # noqa: F821
    row = env.cr.fetchone()  # noqa: F821
    return row[0] if row else None


def int_scalar(sql: str, params: list[object] | None = None) -> int:
    return int(scalar(sql, params) or 0)


def float_scalar(sql: str, params: list[object] | None = None) -> float:
    return float(scalar(sql, params) or 0)


counts = {
    "expense_contracts": int_scalar("SELECT COUNT(*) FROM construction_contract WHERE type = 'in'"),
    "payment_requests": int_scalar("SELECT COUNT(*) FROM payment_request WHERE type = 'pay'"),
    "outflow_request_headers": int_scalar("SELECT COUNT(*) FROM payment_request WHERE note ILIKE '%%[migration:outflow_request_core]%%'"),
    "actual_outflow_headers": int_scalar("SELECT COUNT(*) FROM payment_request WHERE note ILIKE '%%[migration:actual_outflow_core]%%'"),
    "payment_request_lines": int_scalar("SELECT COUNT(*) FROM payment_request_line"),
    "payment_request_lines_with_contract": int_scalar("SELECT COUNT(*) FROM payment_request_line WHERE contract_id IS NOT NULL"),
    "outflow_request_lines_with_contract": int_scalar(
        "SELECT COUNT(*) FROM payment_request_line WHERE legacy_line_id NOT LIKE 'actual_outflow_line:%%' AND contract_id IS NOT NULL"
    ),
    "actual_outflow_lines_with_contract": int_scalar(
        "SELECT COUNT(*) FROM payment_request_line WHERE legacy_line_id LIKE 'actual_outflow_line:%%' AND contract_id IS NOT NULL"
    ),
    "payment_execution_rows": int_scalar("SELECT COUNT(*) FROM sc_payment_execution"),
    "legacy_actual_outflow_line_execution_rows": int_scalar(
        """
        SELECT COUNT(*)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
        """
    ),
    "legacy_actual_outflow_line_execution_with_contract": int_scalar(
        """
        SELECT COUNT(*)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
           AND contract_id IS NOT NULL
        """
    ),
    "expense_contracts_with_payment_lines": int_scalar(
        """
        SELECT COUNT(DISTINCT c.id)
          FROM construction_contract c
          JOIN payment_request_line l ON l.contract_id = c.id
         WHERE c.type = 'in'
        """
    ),
    "expense_contracts_with_payment_execution": int_scalar(
        """
        SELECT COUNT(DISTINCT c.id)
          FROM construction_contract c
          JOIN sc_payment_execution p ON p.contract_id = c.id
         WHERE c.type = 'in'
           AND p.source_origin = 'legacy'
        """
    ),
    "settlement_orders": int_scalar("SELECT COUNT(*) FROM sc_settlement_order"),
    "settlement_orders_with_expense_contract": int_scalar(
        """
        SELECT COUNT(*)
          FROM sc_settlement_order s
          JOIN construction_contract c ON c.id = s.contract_id
         WHERE c.type = 'in'
        """
    ),
    "settlement_adjustment_legacy_rows": int_scalar(
        "SELECT COUNT(*) FROM sc_settlement_adjustment WHERE source_origin = 'legacy'"
    ),
}
amounts = {
    "payment_request_line_current_pay_amount_sum": float_scalar(
        "SELECT COALESCE(SUM(current_pay_amount), 0) FROM payment_request_line WHERE contract_id IS NOT NULL"
    ),
    "actual_outflow_line_current_pay_amount_sum": float_scalar(
        """
        SELECT COALESCE(SUM(current_pay_amount), 0)
          FROM payment_request_line
         WHERE legacy_line_id LIKE 'actual_outflow_line:%%'
           AND contract_id IS NOT NULL
        """
    ),
    "actual_outflow_line_effective_pay_amount_sum": float_scalar(
        """
        SELECT COALESCE(SUM(COALESCE(NULLIF(current_pay_amount, 0), amount, 0)), 0)
          FROM payment_request_line
         WHERE legacy_line_id LIKE 'actual_outflow_line:%%'
           AND contract_id IS NOT NULL
        """
    ),
    "legacy_actual_outflow_line_execution_paid_amount_sum": float_scalar(
        """
        SELECT COALESCE(SUM(paid_amount), 0)
          FROM sc_payment_execution
         WHERE source_origin = 'legacy'
           AND source_kind = 'actual_outflow'
           AND legacy_source_model = 'payment.request.line'
           AND contract_id IS NOT NULL
        """
    ),
    "legacy_settlement_adjustment_signed_amount_sum": float_scalar(
        "SELECT COALESCE(SUM(signed_amount), 0) FROM sc_settlement_adjustment WHERE source_origin = 'legacy'"
    ),
}

errors = []
if counts["payment_requests"] == 0:
    errors.append({"error": "missing_payment_requests"})
if counts["payment_request_lines_with_contract"] == 0:
    errors.append({"error": "missing_contract_linked_payment_request_lines"})
if counts["legacy_actual_outflow_line_execution_with_contract"] == 0:
    errors.append({"error": "missing_contract_linked_payment_execution_projection"})

settlement_boundary = {
    "complete_settlement_order_replayed": counts["settlement_orders_with_expense_contract"] > 0,
    "legacy_adjustment_fact_projected": counts["settlement_adjustment_legacy_rows"] > 0,
    "decision": (
        "settlement_adjustments_projected_complete_settlement_orders_not_supported_by_current_payload"
        if counts["settlement_orders_with_expense_contract"] == 0
        else "settlement_orders_present"
    ),
}

summary = {
    "database": env.cr.dbname,  # noqa: F821
    "counts": counts,
    "amounts": amounts,
    "settlement_boundary": settlement_boundary,
}
status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_expense_contract_payment_fact_acceptance",
    "summary": summary,
    "errors": errors,
    "decision": "expense_contract_payment_facts_materialized" if status == "PASS" else "STOP_REVIEW_REQUIRED",
}

OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
OUTPUT_REPORT.write_text(
    f"""# Business Expense Contract Payment Fact Acceptance v1

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
    "BUSINESS_EXPENSE_CONTRACT_PAYMENT_FACT_ACCEPTANCE="
    + json.dumps(
        {
            "status": status,
            "payment_requests": counts["payment_requests"],
            "payment_request_lines_with_contract": counts["payment_request_lines_with_contract"],
            "legacy_actual_outflow_line_execution_with_contract": counts[
                "legacy_actual_outflow_line_execution_with_contract"
            ],
            "expense_contracts_with_payment_execution": counts["expense_contracts_with_payment_execution"],
            "artifact_root": str(ARTIFACT_ROOT),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
if errors:
    raise RuntimeError(errors)
