# SCBS55 Payload Promotion Queue v1

Status: `PASS`

Source: `docs/migration_alignment/scbs55_replay_payload_gap_report_v1.json`

## Summary

- lanes: `12`
- missing required inputs: `122`
- runtime output backlog: `200`

## Queue

| Priority | Lane | Steps | Missing required inputs | Runtime output backlog | Decision |
|---:|---|---:|---:|---:|---|
| 10 | foundation_manifest | 3 | 1 | 1 | promote_required_inputs_first |
| 20 | user_security_context | 9 | 5 | 5 | promote_required_inputs_first |
| 30 | master_partner_project | 31 | 32 | 55 | promote_required_inputs_first |
| 40 | contract_and_supplier | 29 | 17 | 33 | promote_required_inputs_first |
| 50 | receipt_income | 19 | 9 | 21 | promote_required_inputs_first |
| 60 | outflow_payment | 24 | 12 | 18 | promote_required_inputs_first |
| 70 | finance_accounting | 28 | 24 | 29 | promote_required_inputs_first |
| 80 | materials_tender_purchase | 8 | 8 | 10 | promote_required_inputs_first |
| 90 | attachments_workflow | 6 | 6 | 7 | promote_required_inputs_first |
| 100 | formal_projections | 41 | 5 | 8 | promote_required_inputs_first |
| 110 | runtime_probes | 8 | 0 | 0 | covered_in_current_workspace |
| 999 | unclassified | 15 | 3 | 13 | promote_required_inputs_first |

## Lane Details

### 10 foundation_manifest

- steps: `3`
- missing required inputs: `1`
- runtime output backlog: `1`
- sample missing inputs:
  - `manifest_dry_run` `artifacts/migration/fresh_db_replay_manifest_v1.json`
- sample runtime outputs:
  - `manifest_dry_run` `artifacts/migration/fresh_db_replay_manifest_runner_dry_run_v1.md`

### 20 user_security_context

- steps: `9`
- missing required inputs: `5`
- runtime output backlog: `5`
- sample missing inputs:
  - `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv`
  - `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json`
  - `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv`
  - `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json`
  - `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
- sample runtime outputs:
  - `legacy_user_context_adapter` `artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json`
  - `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_context_replay_write_result_v1.json`
  - `legacy_user_project_scope_adapter` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json`
  - `legacy_user_project_scope_adapter` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
  - `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_write_result_v1.json`

### 30 master_partner_project

- steps: `31`
- missing required inputs: `32`
- runtime output backlog: `55`
- sample missing inputs:
  - `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv`
  - `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv`
  - `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_adapter_result_v1.json`
  - `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
  - `receipt_counterparty_partner_completed` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json`
- sample runtime outputs:
  - `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_rollback_targets_v1.csv`
  - `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_write_result_v1.json`
  - `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv`
  - `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json`
  - `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_rollback_targets_v1.csv`

### 40 contract_and_supplier

- steps: `29`
- missing required inputs: `17`
- runtime output backlog: `33`
- sample missing inputs:
  - `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json`
  - `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_payload_v1.csv`
  - `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv`
  - `contract_header_special_12` `artifacts/migration/contract_12_row_write_authorization_packet_v1.json`
  - `contract_header_special_12` `artifacts/migration/contract_12_row_write_authorization_payload_v1.csv`
- sample runtime outputs:
  - `legacy_labor_subcontract_adapter` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json`
  - `legacy_labor_subcontract_adapter` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_payload_v1.csv`
  - `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_write_result_v1.json`
  - `contract_header_remaining_adapter` `artifacts/migration/fresh_db_contract_remaining_adapter_report_v1.md`
  - `contract_header_remaining_adapter` `artifacts/migration/fresh_db_contract_remaining_adapter_result_v1.json`

### 50 receipt_income

- steps: `19`
- missing required inputs: `9`
- runtime output backlog: `21`
- sample missing inputs:
  - `receipt_header_pending` `artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv`
  - `receipt_invoice_line_replay` `artifacts/migration/fresh_db_receipt_invoice_line_replay_adapter_result_v1.json`
  - `receipt_invoice_line_replay` `artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv`
  - `receipt_invoice_attachment_replay` `artifacts/migration/fresh_db_receipt_invoice_attachment_replay_adapter_result_v1.json`
  - `receipt_invoice_attachment_replay` `artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv`
- sample runtime outputs:
  - `receipt_core_adapter` `artifacts/migration/fresh_db_receipt_core_replay_adapter_result_v1.json`
  - `receipt_core_adapter` `artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv`
  - `receipt_header_pending` `artifacts/migration/fresh_db_receipt_core_post_write_snapshot_v1.csv`
  - `receipt_header_pending` `artifacts/migration/fresh_db_receipt_core_pre_write_snapshot_v1.csv`
  - `receipt_header_pending` `artifacts/migration/fresh_db_receipt_core_rollback_targets_v1.csv`

### 60 outflow_payment

- steps: `24`
- missing required inputs: `12`
- runtime output backlog: `18`
- sample missing inputs:
  - `outflow_request_replay` `artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json`
  - `outflow_request_replay` `artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv`
  - `actual_outflow_replay` `artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json`
  - `actual_outflow_replay` `artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv`
  - `outflow_request_line_replay` `artifacts/migration/fresh_db_outflow_request_line_replay_adapter_result_v1.json`
- sample runtime outputs:
  - `outflow_request_adapter` `artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json`
  - `outflow_request_adapter` `artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv`
  - `outflow_request_replay` `artifacts/migration/fresh_db_outflow_request_replay_write_result_v1.json`
  - `outflow_request_fact_coverage` `artifacts/migration/fresh_db_outflow_request_fact_coverage_write_result_v1.json`
  - `actual_outflow_adapter` `artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json`

### 70 finance_accounting

- steps: `28`
- missing required inputs: `24`
- runtime output backlog: `29`
- sample missing inputs:
  - `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json`
  - `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv`
  - `legacy_account_transaction_replay` `artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json`
  - `legacy_self_funding_replay` `artifacts/migration/fresh_db_legacy_self_funding_replay_adapter_result_v1.json`
  - `legacy_self_funding_replay` `artifacts/migration/fresh_db_legacy_self_funding_replay_payload_v1.csv`
- sample runtime outputs:
  - `legacy_account_master_adapter` `artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json`
  - `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_write_result_v1.json`
  - `legacy_account_transaction_adapter` `artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json`
  - `legacy_account_transaction_replay` `artifacts/migration/fresh_db_legacy_account_transaction_replay_write_result_v1.json`
  - `legacy_self_funding_adapter` `artifacts/migration/fresh_db_legacy_self_funding_replay_adapter_result_v1.json`

### 80 materials_tender_purchase

- steps: `8`
- missing required inputs: `8`
- runtime output backlog: `10`
- sample missing inputs:
  - `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json`
  - `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv`
  - `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv`
  - `legacy_tender_registration_replay` `artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json`
  - `legacy_material_stock_replay` `artifacts/migration/fresh_db_legacy_material_stock_replay_adapter_result_v1.json`
- sample runtime outputs:
  - `legacy_material_catalog_adapter` `artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json`
  - `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_catalog_replay_write_result_v1.json`
  - `legacy_tender_registration_adapter` `artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json`
  - `legacy_tender_registration_replay` `artifacts/migration/fresh_db_legacy_tender_registration_replay_write_result_v1.json`
  - `legacy_material_stock_adapter` `artifacts/migration/fresh_db_legacy_material_stock_replay_adapter_result_v1.json`

### 90 attachments_workflow

- steps: `6`
- missing required inputs: `6`
- runtime output backlog: `7`
- sample missing inputs:
  - `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json`
  - `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv`
  - `legacy_attachment_backfill_replay` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json`
  - `legacy_attachment_backfill_replay` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv`
  - `legacy_workflow_audit_replay` `artifacts/migration/fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json`
- sample runtime outputs:
  - `legacy_file_index_adapter` `artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json`
  - `legacy_file_index_adapter` `artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv`
  - `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_write_result_v1.json`
  - `legacy_attachment_backfill_adapter` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json`
  - `legacy_attachment_backfill_adapter` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv`

### 100 formal_projections

- steps: `41`
- missing required inputs: `5`
- runtime output backlog: `8`
- sample missing inputs:
  - `legacy_project_fund_balance_replay` `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json`
  - `legacy_project_fund_balance_replay` `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv`
  - `legacy_income_invoice_replay` `artifacts/migration/fresh_db_legacy_income_invoice_replay_adapter_result_v1.json`
  - `legacy_construction_diary_line_replay` `artifacts/migration/fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json`
  - `legacy_construction_diary_line_replay` `artifacts/migration/fresh_db_legacy_construction_diary_line_replay_payload_v1.csv`
- sample runtime outputs:
  - `legacy_project_fund_balance_adapter` `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json`
  - `legacy_project_fund_balance_adapter` `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv`
  - `legacy_project_fund_balance_replay` `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_write_result_v1.json`
  - `legacy_income_invoice_adapter` `artifacts/migration/fresh_db_legacy_income_invoice_replay_adapter_result_v1.json`
  - `legacy_income_invoice_replay` `artifacts/migration/fresh_db_legacy_income_invoice_replay_write_result_v1.json`

### 110 runtime_probes

- steps: `8`
- missing required inputs: `0`
- runtime output backlog: `0`

### 999 unclassified

- steps: `15`
- missing required inputs: `3`
- runtime output backlog: `13`
- sample missing inputs:
  - `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json`
  - `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv`
  - `legacy_deduction_adjustment_line_replay` `artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_adapter_result_v1.json`
- sample runtime outputs:
  - `legacy_task_evidence_adapter` `artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json`
  - `legacy_task_evidence_adapter` `artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv`
  - `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_write_result_v1.json`
  - `legacy_attendance_checkin_adapter` `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json`
  - `legacy_attendance_checkin_adapter` `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv`

## Decision

`promote payloads lane-by-lane in priority order; release-package verification remains the blocking gate`
