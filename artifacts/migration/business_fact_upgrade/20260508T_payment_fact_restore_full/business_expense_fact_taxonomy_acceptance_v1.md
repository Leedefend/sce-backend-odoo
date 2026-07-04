# Business Expense Fact Taxonomy Acceptance v1

Status: PASS

## Summary

```json
{
  "database": "sc_partner_acceptance",
  "action_count": 20,
  "menu_count": 29,
  "db_writes": 0,
  "fact_counts": {
    "expense_contracts": 5448,
    "expense_contracts_material": 2409,
    "expense_contracts_normal": 1779,
    "expense_contracts_labor": 439,
    "expense_contracts_rental": 423,
    "expense_contracts_subcontract": 215,
    "expense_contracts_other": 34,
    "expense_contracts_supplement": 2,
    "payment_requests": 25429,
    "payment_request_lines": 31883,
    "actual_outflow_execution": 6750,
    "outflow_request_residual_execution": 962,
    "legacy_payment_residual": 1683,
    "expense_claims": 0,
    "deposit_pay": 0,
    "deposit_refund": 0,
    "deposit_receive": 0,
    "legacy_expense_deposit_outflow": 0,
    "legacy_expense_deposit_refund": 0,
    "legacy_expense_reimbursement_lines": 0,
    "legacy_deduction_adjustment_lines": 13113,
    "legacy_tax_deductions": 0,
    "legacy_fund_confirmation_lines": 0,
    "financing_loan_registration": 0,
    "borrowing_requests": 0,
    "legacy_purchase_contracts": 46,
    "legacy_supplier_contract_pricing": 5345
  }
}
```

## Errors

```json
[]
```

## Decision

`business_expense_fact_taxonomy_ready`
