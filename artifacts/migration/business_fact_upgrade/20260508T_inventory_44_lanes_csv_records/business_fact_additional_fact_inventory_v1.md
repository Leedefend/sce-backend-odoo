# Business Fact Additional Fact Inventory v1

Status: PASS

## Summary

```json
{
  "source_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration",
  "artifact_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/business_fact_upgrade/20260508T_inventory_44_lanes_csv_records",
  "lane_count": 44,
  "present_lanes": 44,
  "missing_lanes": 0,
  "pass_lanes": 44,
  "non_pass_lanes": 0,
  "payload_declared_lanes": 43,
  "payload_present_lanes": 43,
  "payload_missing_lanes": 0
}
```

## Lanes

```json
[
  {
    "lane": "receipt_core",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_receipt_core_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_core_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 5355,
      "expected_rows": 5355
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "",
    "payload_presence": "not_declared",
    "payload_data_rows": null,
    "payload_expected_rows": null,
    "payload_checks": []
  },
  {
    "lane": "actual_outflow",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_actual_outflow_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 12463,
      "expected_rows": 12463
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 12463,
    "payload_expected_rows": 12463,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 12463,
        "expected_rows": 12463
      }
    ]
  },
  {
    "lane": "actual_outflow_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_actual_outflow_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_line_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 15966,
      "distinct_parent_actual_outflow_ids": 10662,
      "expected_rows": 15966
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 15966,
    "payload_expected_rows": 15966,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 15966,
        "expected_rows": 15966
      }
    ]
  },
  {
    "lane": "actual_outflow_residual",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_actual_outflow_residual_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_residual_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 10662,
      "expected_rows": 10662
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 10662,
    "payload_expected_rows": 10662,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 10662,
        "expected_rows": 10662
      }
    ]
  },
  {
    "lane": "outflow_request",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_outflow_request_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 12284,
      "expected_rows": 12284
    },
    "amounts": {},
    "decisions": {
      "decision": "outflow_request_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 12284,
    "payload_expected_rows": 12284,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 12284,
        "expected_rows": 12284
      }
    ]
  },
  {
    "lane": "outflow_request_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_outflow_request_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_line_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 15917,
      "expected_rows": 15917
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 15917,
    "payload_expected_rows": 15917,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 15917,
        "expected_rows": 15917
      }
    ]
  },
  {
    "lane": "legacy_receipt_income",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_receipt_income_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_income_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 7220,
      "expected_rows": 7220
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 7220,
    "payload_expected_rows": 7220,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 7220,
        "expected_rows": 7220
      }
    ]
  },
  {
    "lane": "legacy_receipt_residual",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_receipt_residual_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json",
    "row_counts": {
      "active_rows": 7363,
      "receipt_rows": 7412,
      "total_rows": 7412
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_receipt_residual_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 7412,
    "payload_expected_rows": 7412,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 7412,
        "expected_rows": 7412
      }
    ]
  },
  {
    "lane": "legacy_invoice_tax",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_invoice_tax_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_tax_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 5920,
      "expected_rows": 5920
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_tax_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 5920,
    "payload_expected_rows": 5920,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_tax_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 5920,
        "expected_rows": 5920
      }
    ]
  },
  {
    "lane": "receipt_invoice_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_receipt_invoice_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_line_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 4454,
      "expected_rows": 4454
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 4454,
    "payload_expected_rows": 4454,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 4454,
        "expected_rows": 4454
      }
    ]
  },
  {
    "lane": "receipt_invoice_attachment",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_receipt_invoice_attachment_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_attachment_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 1079,
      "expected_rows": 1079
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 1079,
    "payload_expected_rows": 1079,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 1079,
        "expected_rows": 1079
      }
    ]
  },
  {
    "lane": "legacy_invoice_registration_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_invoice_registration_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 25393,
      "header_rows": 16616,
      "active_header_rows": 16075,
      "orphan_line_rows": 113
    },
    "amounts": {
      "amount_no_tax": "2170459215.9000",
      "tax_amount": "115434418.0800",
      "amount_total": "2282867004.1100"
    },
    "decisions": {
      "decision": "legacy_invoice_registration_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 25393,
    "payload_expected_rows": 25393,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 25393,
        "expected_rows": 25393
      }
    ]
  },
  {
    "lane": "legacy_invoice_surcharge",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_invoice_surcharge_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter_result_v1.json",
    "row_counts": {
      "expected_rows": 27053,
      "output_rows": 4540,
      "input_rows": 22513
    },
    "amounts": {
      "output_surcharge_amount": 20595859.4964,
      "input_surcharge_amount": 13328329.2112
    },
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 27053,
    "payload_expected_rows": 27053,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 27053,
        "expected_rows": 27053
      }
    ]
  },
  {
    "lane": "legacy_tax_deduction",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_tax_deduction_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_tax_deduction_replay_adapter_result_v1.json",
    "row_counts": {
      "expected_rows": 4915
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_tax_deduction_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 4915,
    "payload_expected_rows": 4915,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_tax_deduction_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 4915,
        "expected_rows": 4915
      }
    ]
  },
  {
    "lane": "legacy_fund_confirmation_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_fund_confirmation_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 13398,
      "header_rows": 2655,
      "active_header_rows": 2595,
      "orphan_line_rows": 0
    },
    "amounts": {
      "current_actual_amount": "260848353.6900",
      "accumulated_actual_amount": "52447133.2600"
    },
    "decisions": {
      "decision": "legacy_fund_confirmation_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 13398,
    "payload_expected_rows": 13398,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 13398,
        "expected_rows": 13398
      }
    ]
  },
  {
    "lane": "legacy_fund_daily_snapshot",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_fund_daily_snapshot_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 496,
      "expected_rows": 496
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 496,
    "payload_expected_rows": 496,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 496,
        "expected_rows": 496
      }
    ]
  },
  {
    "lane": "legacy_payment_residual",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_payment_residual_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_payment_residual_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 27275,
      "outflow_request_rows": 13646,
      "actual_outflow_rows": 13629
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_payment_residual_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 27275,
    "payload_expected_rows": 27275,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 27275,
        "expected_rows": 27275
      }
    ]
  },
  {
    "lane": "legacy_self_funding",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_self_funding_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_self_funding_replay_adapter_result_v1.json",
    "row_counts": {
      "expected_rows": 3728
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_self_funding_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 3728,
    "payload_expected_rows": 3728,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_self_funding_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 3728,
        "expected_rows": 3728
      }
    ]
  },
  {
    "lane": "legacy_expense_deposit",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_expense_deposit_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_deposit_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 11167,
      "expected_rows": 11167
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_deposit_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 11167,
    "payload_expected_rows": 11167,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_deposit_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 11167,
        "expected_rows": 11167
      }
    ]
  },
  {
    "lane": "legacy_expense_reimbursement_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_expense_reimbursement_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 3589,
      "header_rows": 1866,
      "active_header_rows": 1845,
      "orphan_line_rows": 2
    },
    "amounts": {
      "line_amount": "11888847.9600",
      "header_approved_amount": "11869461.6600"
    },
    "decisions": {
      "decision": "legacy_expense_reimbursement_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 3589,
    "payload_expected_rows": 3589,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 3589,
        "expected_rows": 3589
      }
    ]
  },
  {
    "lane": "legacy_financing_loan",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_financing_loan_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_financing_loan_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 318,
      "expected_rows": 318
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_financing_loan_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 318,
    "payload_expected_rows": 318,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_financing_loan_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 318,
        "expected_rows": 318
      }
    ]
  },
  {
    "lane": "legacy_account_master",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_account_master_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json",
    "row_counts": {
      "account_rows": 117
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_account_master_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 117,
    "payload_expected_rows": 117,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 117,
        "expected_rows": 117
      }
    ]
  },
  {
    "lane": "legacy_account_transaction",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_account_transaction_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json",
    "row_counts": {
      "rows": 39707
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_account_transaction_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 39707,
    "payload_expected_rows": 39707,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 39707,
        "expected_rows": 39707
      }
    ]
  },
  {
    "lane": "legacy_fund_daily_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_fund_daily_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 7754,
      "header_rows": 511,
      "active_header_rows": 496,
      "line_rows": 7754,
      "orphan_line_rows": 0
    },
    "amounts": {
      "daily_income_sum": "1524275095.6800",
      "daily_expense_sum": "1317155332.1900",
      "current_account_balance_sum": "5693334440.5800"
    },
    "decisions": {
      "decision": "legacy_fund_daily_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 7754,
    "payload_expected_rows": 7754,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 7754,
        "expected_rows": 7754
      }
    ]
  },
  {
    "lane": "legacy_project_fund_balance",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_project_fund_balance_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json",
    "row_counts": {
      "expected_rows": 755
    },
    "amounts": {
      "actual_available_balance": -2586337.86
    },
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 755,
    "payload_expected_rows": 755,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 755,
        "expected_rows": 755
      }
    ]
  },
  {
    "lane": "legacy_deduction_adjustment_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_deduction_adjustment_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 13521,
      "header_rows": 2636,
      "active_header_rows": 2572,
      "orphan_line_rows": 0
    },
    "amounts": {
      "current_actual_amount": "264765389.5800",
      "current_planned_amount": "264765389.5800"
    },
    "decisions": {
      "decision": "legacy_deduction_adjustment_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 13521,
    "payload_expected_rows": 13521,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 13521,
        "expected_rows": 13521
      }
    ]
  },
  {
    "lane": "legacy_construction_diary_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_construction_diary_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 5687,
      "header_rows": 4340,
      "active_header_rows": 4339,
      "orphan_line_rows": 18,
      "with_attachment_path_rows": 6
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_construction_diary_line_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_construction_diary_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 5687,
    "payload_expected_rows": 5687,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_construction_diary_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 5687,
        "expected_rows": 5687
      }
    ]
  },
  {
    "lane": "legacy_task_evidence",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_task_evidence_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 78822,
      "active_rows": 74028,
      "done_rows": 709,
      "read_rows": 45438
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_task_evidence_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 78822,
    "payload_expected_rows": 78822,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 78822,
        "expected_rows": 78822
      }
    ]
  },
  {
    "lane": "legacy_file_index",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_file_index_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json",
    "row_counts": {
      "base_system_file_rows": 126967,
      "bill_file_rows": 51964,
      "total_rows": 178931,
      "base_system_file_active_rows": 125213,
      "bill_file_active_rows": 49148
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_file_index_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 178931,
    "payload_expected_rows": 178931,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 178931,
        "expected_rows": 178931
      }
    ]
  },
  {
    "lane": "legacy_material_catalog",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_material_catalog_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json",
    "row_counts": {
      "category_rows": 130624,
      "detail_rows": 2279734
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_material_catalog_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv;/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 2410358,
    "payload_expected_rows": 2410358,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 130624,
        "expected_rows": 130624
      },
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 2279734,
        "expected_rows": 2279734
      }
    ]
  },
  {
    "lane": "legacy_supplier_contract_pricing",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_supplier_contract_pricing_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_adapter_result_v1.json",
    "row_counts": {
      "expected_rows": 5345,
      "pricing_method_rows": 4677,
      "distinct_pricing_methods": 17
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 5345,
    "payload_expected_rows": 5345,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 5345,
        "expected_rows": 5345
      }
    ]
  },
  {
    "lane": "legacy_purchase_contract",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_purchase_contract_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json",
    "row_counts": {
      "total_rows": 49,
      "active_rows": 46,
      "project_count": 2,
      "partner_text_count": 27
    },
    "amounts": {
      "amount_sum": "12334556.9200"
    },
    "decisions": {
      "decision": "legacy_purchase_contract_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 49,
    "payload_expected_rows": 49,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 49,
        "expected_rows": 49
      }
    ]
  },
  {
    "lane": "supplier_contract",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_supplier_contract_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 5301,
      "expected_rows": 5301
    },
    "amounts": {},
    "decisions": {
      "decision": "supplier_contract_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 5301,
    "payload_expected_rows": 5301,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 5301,
        "expected_rows": 5301
      }
    ]
  },
  {
    "lane": "supplier_contract_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_supplier_contract_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_line_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 5065,
      "expected_rows": 5065
    },
    "amounts": {},
    "decisions": {
      "decision": "supplier_contract_line_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 5065,
    "payload_expected_rows": 5065,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_supplier_contract_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 5065,
        "expected_rows": 5065
      }
    ]
  },
  {
    "lane": "legacy_attachment_backfill",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_attachment_backfill_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 18458,
      "expected_rows": 18458
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 18458,
    "payload_expected_rows": 18458,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 18458,
        "expected_rows": 18458
      }
    ]
  },
  {
    "lane": "legacy_workflow_audit",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_workflow_audit_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 79702,
      "expected_rows": 79702
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_workflow_audit_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 79702,
    "payload_expected_rows": 79702,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_workflow_audit_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 79702,
        "expected_rows": 79702
      }
    ]
  },
  {
    "lane": "legacy_user_context",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_user_context_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json",
    "row_counts": {
      "department_rows": 828,
      "profile_rows": 101,
      "role_rows": 330
    },
    "amounts": {},
    "decisions": {},
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv;/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv;/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 1259,
    "payload_expected_rows": 1259,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 828,
        "expected_rows": 828
      },
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 101,
        "expected_rows": 101
      },
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 330,
        "expected_rows": 330
      }
    ]
  },
  {
    "lane": "legacy_user_project_scope",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_legacy_user_project_scope_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json",
    "row_counts": {
      "current_rows": 20000,
      "history_rows": 70871,
      "total_rows": 90871
    },
    "amounts": {},
    "decisions": {
      "decision": "legacy_user_project_scope_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 90871,
    "payload_expected_rows": 90871,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 90871,
        "expected_rows": 90871
      }
    ]
  },
  {
    "lane": "project_anchor",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_project_anchor_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_anchor_replay_adapter_result_v1.json",
    "row_counts": {
      "asset_xml_rows": 755,
      "project_master_source_rows": 755,
      "contract_visible_project_anchor_rows": 43,
      "created_evidence_rows": 798,
      "replay_payload_rows": 798
    },
    "amounts": {
      "deferred_contract_project_gap_amount_sum": "43266877.41"
    },
    "decisions": {
      "decision": "project_anchor_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 798,
    "payload_expected_rows": 798,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 798,
        "expected_rows": 798
      }
    ]
  },
  {
    "lane": "project_member_neutral",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_project_member_neutral_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_member_neutral_replay_adapter_result_v1.json",
    "row_counts": {
      "completed_source_rows": 21390,
      "replay_payload_rows": 21390
    },
    "amounts": {},
    "decisions": {
      "decision": "project_member_neutral_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 21390,
    "payload_expected_rows": 21390,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 21390,
        "expected_rows": 21390
      }
    ]
  },
  {
    "lane": "partner_l4",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_partner_l4_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_partner_l4_replay_adapter_result_v1.json",
    "row_counts": {
      "created_evidence_rows": 6842,
      "replay_payload_rows": 6842,
      "write_result_files": 11
    },
    "amounts": {},
    "decisions": {
      "decision": "partner_l4_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 6842,
    "payload_expected_rows": 6842,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_partner_l4_business_fit_payload_v1.csv",
        "presence": "present",
        "data_rows": 6842,
        "expected_rows": 6842
      }
    ]
  },
  {
    "lane": "contract_counterparty_partner",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_contract_counterparty_partner_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_counterparty_partner_replay_adapter_result_v1.json",
    "row_counts": {
      "candidate_contract_rows": 439,
      "replay_payload_rows": 88,
      "expected_rows": 88
    },
    "amounts": {},
    "decisions": {
      "decision": "contract_counterparty_partner_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 88,
    "payload_expected_rows": 88,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 88,
        "expected_rows": 88
      }
    ]
  },
  {
    "lane": "receipt_counterparty_partner",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_receipt_counterparty_partner_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json",
    "row_counts": {
      "candidate_receipt_rows": 1944,
      "replay_payload_rows": 250,
      "expected_rows": 250
    },
    "amounts": {},
    "decisions": {
      "decision": "receipt_counterparty_partner_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 250,
    "payload_expected_rows": 250,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 250,
        "expected_rows": 250
      }
    ]
  },
  {
    "lane": "contract_line",
    "presence": "present",
    "status": "PASS",
    "mode": "fresh_db_contract_line_replay_adapter",
    "source_artifact": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_line_replay_adapter_result_v1.json",
    "row_counts": {
      "replay_payload_rows": 1441,
      "expected_rows": 1441
    },
    "amounts": {},
    "decisions": {
      "decision": "contract_line_replay_payload_ready"
    },
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_line_replay_payload_v1.csv",
    "payload_presence": "present",
    "payload_data_rows": 1441,
    "payload_expected_rows": 1441,
    "payload_checks": [
      {
        "csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_contract_line_replay_payload_v1.csv",
        "presence": "present",
        "data_rows": 1441,
        "expected_rows": 1441
      }
    ]
  }
]
```

## Errors

```json
[]
```

## Decision

`additional_business_fact_inventory_ready`
