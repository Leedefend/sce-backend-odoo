# Business Fact Acceptance Bundle Summary v1

Status: PASS

## Summary

```json
{
  "artifact_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/business_fact_upgrade/20260508T113829",
  "postcheck": {
    "presence": "present",
    "status": "PASS",
    "contract_total": 6985,
    "income_contracts": 1537,
    "expense_contracts": 5448,
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
  },
  "expense_contract_subtypes": {
    "presence": "present",
    "status": "PASS",
    "supplier_subject_counts": {
      "材料合同": 2409,
      "正常合同": 1779,
      "租赁合同": 423,
      "分包合同": 215,
      "劳务合同": 439,
      "其他合同": 34,
      "补充合同": 2
    },
    "recommended_subjects": [
      "材料合同",
      "正常合同",
      "劳务合同",
      "租赁合同",
      "分包合同",
      "其他合同",
      "补充合同"
    ]
  },
  "expense_payment_facts": {
    "presence": "present",
    "status": "PASS",
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
}
```

## Errors

```json
[]
```

## Decision

`business_fact_acceptance_bundle_passed`
