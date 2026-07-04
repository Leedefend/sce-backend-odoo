# Business Fact Acceptance Bundle Summary v1

Status: PASS

## Summary

```json
{
  "artifact_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/business_fact_upgrade/20260508T_acceptance_expense_taxonomy_bundle",
  "postcheck": {
    "presence": "present",
    "status": "PASS",
    "contract_total": 6850,
    "income_contracts": 1541,
    "expense_contracts": 5309,
    "contract_lines": 6566,
    "visible_fact_mismatches": 0,
    "visible_balance_observations": 5
  },
  "cleanup": {
    "presence": "present",
    "status": "PASS",
    "visible_balance_observations": 5,
    "classification_counts": {
      "legacy_visible_negative_balance_without_transaction_fact": 3,
      "legacy_visible_partial_or_closed_balance_without_transaction_fact": 2
    },
    "invoice_receipt_mismatches": 0,
    "db_writes": 0
  },
  "legacy_source": {
    "presence": "present",
    "status": "PASS",
    "source_contract_rows_found": 5,
    "receipt_linked_rows": 0,
    "invoice_linked_rows": 0,
    "decisions": {
      "legacy_contract_header_only_no_linked_transaction_detail": 5
    }
  },
  "additional_facts": {
    "presence": "present",
    "status": "PASS",
    "lane_count": 44,
    "present_lanes": 44,
    "missing_lanes": 0,
    "pass_lanes": 44,
    "payload_present_lanes": 43,
    "payload_missing_lanes": 0
  },
  "expense_taxonomy": {
    "presence": "present",
    "status": "PASS",
    "action_count": 13,
    "menu_count": 22,
    "db_writes": 0,
    "fact_counts": {
      "expense_contracts": 5309,
      "payment_requests": 0,
      "payment_request_lines": 0,
      "actual_outflow_execution": 0,
      "outflow_request_residual_execution": 0,
      "legacy_payment_residual": 0,
      "expense_claims": 0,
      "deposit_pay": 0,
      "deposit_refund": 0,
      "deposit_receive": 0,
      "legacy_expense_deposit_outflow": 0,
      "legacy_expense_deposit_refund": 0,
      "legacy_expense_reimbursement_lines": 0,
      "legacy_deduction_adjustment_lines": 0,
      "legacy_tax_deductions": 0,
      "legacy_fund_confirmation_lines": 0,
      "financing_loan_registration": 0,
      "borrowing_requests": 0,
      "legacy_purchase_contracts": 46,
      "legacy_supplier_contract_pricing": 0
    }
  }
}
```

## Errors

```json
[]
```

## Decision

`business_fact_acceptance_bundle_passed`
