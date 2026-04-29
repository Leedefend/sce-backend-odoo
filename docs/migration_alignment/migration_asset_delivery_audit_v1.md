# Migration Asset Delivery Audit v1

Status: `FAIL`

## Scope

Read-only audit for production delivery packaging. This report does not
connect to Odoo, execute replay writes, or mutate migration assets.

## Summary

- catalog packages: `23`
- asset files: `95`
- referenced files: `93`
- unreferenced files: `2`
- total asset size MB: `347.26`
- replay steps: `163`
- required replay artifacts: `118`
- missing required replay artifacts: `118`
- duplicate materialized parts: `0`

## Decision

- blockers: `1`
- packaging actions: `1`

### Blockers

- packaged replay frozen artifacts are missing

### Missing Required Replay Artifacts

- `artifacts/migration/contract_12_row_write_authorization_packet_v1.json`
- `artifacts/migration/contract_12_row_write_authorization_payload_v1.csv`
- `artifacts/migration/contract_partner_source_57_design_rows_v1.csv`
- `artifacts/migration/fresh_db_actual_outflow_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_actual_outflow_residual_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv`
- `artifacts/migration/fresh_db_contract_counterparty_partner_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_contract_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_contract_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv`
- `artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_construction_diary_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_expense_deposit_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_expense_deposit_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_financing_loan_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_financing_loan_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_fund_confirmation_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_fund_daily_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_fund_daily_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_fund_daily_snapshot_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_invoice_tax_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_invoice_tax_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_payment_residual_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_personnel_movement_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_receipt_income_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_receipt_residual_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_salary_line_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_self_funding_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_self_funding_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_tax_deduction_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_tax_deduction_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_user_profile_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json`
- `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv`
- `artifacts/migration/fresh_db_legacy_workflow_audit_replay_adapter_result_v1.json`
- ... +38 more

### Packaging Actions

- classify unreferenced migration asset files as delivery evidence or remove from release package

## Entrypoints

- `history.continuity.rehearse`: `True`
- `history.continuity.replay`: `True`
- `history.production.fresh_init`: `True`
- production calls one-click replay: `True`
- `HISTORY_CONTINUITY_START_AT`: `True`

## Duplicate Materialized Parts

- none

## Unreferenced Asset Files

- `migration_assets/manifest/migration_asset_coverage_snapshot_v1.json`
- `migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json`

## Large Files

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml`: `120.01 MB`
- `migration_assets/manifest/legacy_workflow_audit_external_id_manifest_v1.json`: `31.06 MB`
- `migration_assets/20_business/outflow_request_line/outflow_request_line_v1.xml`: `18.34 MB`
- `migration_assets/30_relation/project_member/project_member_neutral_v1.xml`: `16.82 MB`
- `migration_assets/30_relation/legacy_attachment_backfill/legacy_attachment_backfill_v1.xml`: `14.52 MB`
- `migration_assets/30_relation/legacy_expense_deposit/legacy_expense_deposit_v1.xml`: `13.18 MB`
- `migration_assets/20_business/actual_outflow/actual_outflow_core_v1.xml`: `10.05 MB`

## Output

- JSON: `artifacts/migration/migration_asset_delivery_audit_v1.json`
