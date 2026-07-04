# Business Fact Acceptance Bundle Summary v1

Status: PASS

## Summary

```json
{
  "artifact_root": "artifacts/migration/business_fact_upgrade/20260508T114027",
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
    "lane_count": 52,
    "present_lanes": 52,
    "missing_lanes": 0,
    "pass_lanes": 52,
    "payload_present_lanes": 51,
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
      "payment_requests": 25447,
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
  },
  "attachment_custody": {
    "presence": "present",
    "status": "PASS",
    "legacy_file_index_rows": 178931,
    "legacy_url_attachments": 19537,
    "receipt_invoice_attachment_runtime_records": 1079,
    "legacy_attachment_backfill_runtime_records": 18458,
    "gap_count": 0
  },
  "business_fact_residual": {
    "presence": "present",
    "status": "PASS",
    "input_rows": 103258,
    "after": 103258,
    "active_rows": 103057,
    "source_database_counts": {
      "LegacyDb": 79525,
      "LegacyScbs20260417": 23733
    },
    "family_counts": {
      "t": 23636,
      "pm": 21776,
      "cgpt": 13981,
      "office_admin": 10777,
      "labor_subcontract": 8352,
      "lease_equipment": 7083,
      "base": 5055,
      "zlgl": 2052,
      "d": 1483,
      "sggl": 1469,
      "sgbw": 1439,
      "cgxbj": 1259,
      "a": 1066,
      "gzgl": 778,
      "c": 696,
      "dataspider": 469,
      "cwgl": 442,
      "jhjrz": 344,
      "xmgl": 229,
      "xm": 114,
      "material_stock": 95,
      "project_settlement": 89,
      "bid_tender": 84,
      "pj": 66,
      "zyjx": 49,
      "gdzc": 46,
      "yszj": 43,
      "wz": 38,
      "aqgl": 35,
      "yt": 32,
      "cdjx": 24,
      "invoice": 21,
      "system": 16,
      "xmzl": 16,
      "other": 14,
      "ws": 14,
      "lwjhgl": 13,
      "payment_fund": 12,
      "xakw": 12,
      "jggl": 10,
      "htgl": 8,
      "bgoa": 6,
      "jcht": 5,
      "zzxt": 4,
      "xmzhgl": 3,
      "zhbg": 2,
      "zjsz": 1
    },
    "source_table_count": 637,
    "manifest_source_table_count": 637,
    "source_table_count_mismatch_count": 0,
    "coverage": {
      "expected_rows": 103258,
      "actual_rows": 103258,
      "expected_active_rows": null,
      "actual_active_rows": 103057,
      "manifest_source_table_count": 637,
      "actual_source_table_count": 637,
      "source_table_count_mismatch_count": 0,
      "source_table_count_mismatches": [],
      "row_delta": 0,
      "active_row_delta": null
    }
  },
  "business_fact_residual_screen": {
    "presence": "present",
    "status": "PASS",
    "residual_rows": 103258,
    "residual_table_count": 637,
    "specialized_source_table_matched_rows": 10064,
    "residual_only_source_table_rows": 93194,
    "next_assetization_candidate_rows": 766,
    "next_assetization_candidate_tables": 33,
    "band_row_counts": {
      "context_candidate": 54582,
      "inactive_reference_only": 20,
      "next_assetization_candidate": 766,
      "raw_context_only": 37826,
      "related_specialized_source_table": 10064
    }
  },
  "full_legacy_loss_scan": {
    "presence": "present",
    "status": "PASS",
    "non_empty_tables": 1128,
    "candidate_tables": 347,
    "candidate_rows": 79525,
    "top_candidate": "YSZJ_CZBS_CZQDBS"
  },
  "remaining_fact_family_screen": {
    "presence": "present",
    "status": "PASS",
    "screened_tables": 78,
    "screened_rows": 10479,
    "screened_active_rows": 10438,
    "top_family": "labor_subcontract"
  },
  "multi_db_fact_scan": {
    "presence": "present",
    "status": "PASS",
    "source_count": 2,
    "candidate_tables": 637,
    "candidate_rows": 103258,
    "screened_tables": 154,
    "screened_rows": 22006,
    "screened_active_rows": 21922,
    "sources": [
      {
        "artifact_root": "artifacts/migration/business_fact_upgrade/20260508T114027",
        "candidate_rows": 79525,
        "candidate_tables": 347,
        "container": "legacy-mssql-restore",
        "database": "LegacyDb",
        "full_scan_status": "PASS",
        "label": "main",
        "non_empty_tables": 1128,
        "remaining_family_status": "PASS",
        "screened_active_rows": 10438,
        "screened_rows": 10479,
        "screened_tables": 78,
        "top_candidate": "YSZJ_CZBS_CZQDBS",
        "top_family": "labor_subcontract"
      },
      {
        "artifact_root": "artifacts/migration/business_fact_upgrade/20260508T114027/scbs",
        "candidate_rows": 23733,
        "candidate_tables": 290,
        "container": "legacy-mssql-scbs",
        "database": "LegacyScbs20260417",
        "full_scan_status": "PASS",
        "label": "scbs",
        "non_empty_tables": 710,
        "remaining_family_status": "PASS",
        "screened_active_rows": 11484,
        "screened_rows": 11527,
        "screened_tables": 76,
        "top_candidate": "D_SMWZ_WZ_XSHTFB_XSHTFB_XSHTFB",
        "top_family": "lease_equipment"
      }
    ]
  },
  "multi_db_key_collision": {
    "presence": "present",
    "status": "PASS",
    "common_candidate_tables": 171,
    "checked_tables": 25,
    "collision_table_count": 17,
    "collision_key_sample_count": 1433,
    "requires_source_database_in_replay_key": true,
    "decision": "source_database_dimension_required"
  }
}
```

## Errors

```json
[]
```

## Decision

`business_fact_acceptance_bundle_passed`
