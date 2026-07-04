# Business Expense Contract Payment Fact Acceptance v1

Status: PASS

## Summary

```json
{
  "database": "sc_partner_acceptance",
  "counts": {
    "expense_contracts": 5448,
    "payment_requests": 25429,
    "outflow_request_headers": 12284,
    "actual_outflow_headers": 13145,
    "payment_request_lines": 31883,
    "payment_request_lines_with_contract": 13069,
    "outflow_request_lines_with_contract": 6662,
    "actual_outflow_lines_with_contract": 6407,
    "payment_execution_rows": 7712,
    "legacy_actual_outflow_line_execution_rows": 6347,
    "legacy_actual_outflow_line_execution_with_contract": 6347,
    "expense_contracts_with_payment_lines": 4257,
    "expense_contracts_with_payment_execution": 4013,
    "settlement_orders": 0,
    "settlement_orders_with_expense_contract": 0,
    "settlement_adjustment_legacy_rows": 13521
  },
  "amounts": {
    "payment_request_line_current_pay_amount_sum": 2714478973.41,
    "actual_outflow_line_current_pay_amount_sum": 1465089783.61,
    "actual_outflow_line_effective_pay_amount_sum": 1437240283.18,
    "legacy_actual_outflow_line_execution_paid_amount_sum": 1465089783.61,
    "legacy_settlement_adjustment_signed_amount_sum": -264765389.58
  },
  "settlement_boundary": {
    "complete_settlement_order_replayed": false,
    "legacy_adjustment_fact_projected": true,
    "decision": "settlement_adjustments_projected_complete_settlement_orders_not_supported_by_current_payload"
  }
}
```

## Errors

```json
[]
```

## Decision

`expense_contract_payment_facts_materialized`
