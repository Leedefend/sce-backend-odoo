# Business Fact Additional Fact Inventory v1

Status: PASS

## Summary

```json
{
  "source_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration",
  "artifact_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/business_fact_upgrade/20260508T_acceptance_additional_facts",
  "lane_count": 14,
  "present_lanes": 14,
  "missing_lanes": 0,
  "pass_lanes": 14,
  "non_pass_lanes": 0
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
    "payload_csv": ""
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_outflow_request_line_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_tax_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_tax_deduction_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv"
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
    "payload_csv": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv"
  }
]
```

## Errors

```json
[]
```

## Decision

`additional_business_fact_inventory_ready`
