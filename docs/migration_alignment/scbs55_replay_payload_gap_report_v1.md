# SCBS55 Replay Payload Gap Report v1

Status: `PASS_WITH_GAPS`

## Summary

- oneclick: `scripts/migration/history_continuity_oneclick.sh`
- steps: `221`
- adapter steps: `69`
- adapters with packaged outputs: `0`
- required missing inputs: `122`
- runtime outputs not currently packaged: `240`

## Step Kinds

- `adapter`: `69`
- `formal_projection`: `42`
- `normalization`: `6`
- `other`: `18`
- `probe`: `16`
- `write_replay`: `70`

## Step Scope

- `optional_or_recovery`: `26`
- `required`: `195`

## Missing Required Inputs

- `manifest_dry_run` `artifacts/migration/fresh_db_replay_manifest_v1.json`
- `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_department_replay_payload_v1.csv`
- `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json`
- `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_role_replay_payload_v1.csv`
- `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json`
- `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
- `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json`
- `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv`
- `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_payload_v1.csv`
- `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_payload_v1.csv`
- `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json`
- `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_payload_v1.csv`
- `legacy_account_transaction_replay` `artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json`
- `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json`
- `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_category_replay_payload_v1.csv`
- `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_detail_replay_payload_v1.csv`
- `legacy_tender_registration_replay` `artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json`
- `legacy_material_stock_replay` `artifacts/migration/fresh_db_legacy_material_stock_replay_adapter_result_v1.json`
- `legacy_material_stock_replay` `artifacts/migration/fresh_db_legacy_material_stock_replay_payload_v1.csv`
- `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json`
- `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_payload_v1.csv`
- `legacy_equipment_lease_replay` `artifacts/migration/fresh_db_legacy_equipment_lease_replay_adapter_result_v1.json`
- `legacy_equipment_lease_replay` `artifacts/migration/fresh_db_legacy_equipment_lease_replay_payload_v1.csv`
- `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json`
- `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv`
- `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_adapter_result_v1.json`
- `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
- `receipt_counterparty_partner_completed` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_adapter_result_v1.json`
- `receipt_counterparty_partner_completed` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv`
- `project_member_neutral_adapter` `artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv`
- `project_member_neutral_adapter` `artifacts/migration/project_member_neutral_34_write_result_v1.json`
- `project_member_neutral_completed` `artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv`
- `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv`
- `contract_12_missing_partner_anchors` `artifacts/migration/contract_12_row_write_authorization_payload_v1.csv`
- `contract_header_special_12` `artifacts/migration/contract_12_row_write_authorization_packet_v1.json`
- `contract_header_special_12` `artifacts/migration/contract_12_row_write_authorization_payload_v1.csv`
- `contract_header_retry_57` `artifacts/migration/contract_partner_source_57_design_rows_v1.csv`
- `contract_header_retry_57` `artifacts/migration/fresh_db_contract_partner_12_anchor_replay_resolution_v1.csv`
- `legacy_purchase_contract_replay` `artifacts/migration/fresh_db_legacy_purchase_contract_replay_adapter_result_v1.json`
- `legacy_purchase_contract_replay` `artifacts/migration/fresh_db_legacy_purchase_contract_replay_payload_v1.csv`
- `contract_line_completed` `artifacts/migration/fresh_db_contract_line_replay_adapter_result_v1.json`
- `contract_line_completed` `artifacts/migration/fresh_db_contract_line_replay_payload_v1.csv`
- `supplier_partner_targeted_adapter` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv`
- `supplier_partner_targeted_adapter` `artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv`
- `supplier_partner_targeted_replay` `artifacts/migration/history_supplier_partner_targeted_replay_payload_v1.csv`
- `supplier_contract_completed` `artifacts/migration/fresh_db_supplier_contract_replay_adapter_result_v1.json`
- `supplier_contract_completed` `artifacts/migration/fresh_db_supplier_contract_replay_payload_v1.csv`
- `supplier_contract_line_completed` `artifacts/migration/fresh_db_supplier_contract_line_replay_adapter_result_v1.json`
- `supplier_contract_line_completed` `artifacts/migration/fresh_db_supplier_contract_line_replay_payload_v1.csv`
- `receipt_header_pending` `artifacts/migration/fresh_db_receipt_write_design_payload_v1.csv`
- `receipt_invoice_line_replay` `artifacts/migration/fresh_db_receipt_invoice_line_replay_adapter_result_v1.json`
- `receipt_invoice_line_replay` `artifacts/migration/fresh_db_receipt_invoice_line_replay_payload_v1.csv`
- `receipt_invoice_attachment_replay` `artifacts/migration/fresh_db_receipt_invoice_attachment_replay_adapter_result_v1.json`
- `receipt_invoice_attachment_replay` `artifacts/migration/fresh_db_receipt_invoice_attachment_replay_payload_v1.csv`
- `outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
- `outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv`
- `outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv`
- `outflow_partner_targeted_replay` `artifacts/migration/history_outflow_partner_targeted_replay_payload_v1.csv`
- `outflow_request_replay` `artifacts/migration/fresh_db_outflow_request_replay_adapter_result_v1.json`
- `outflow_request_replay` `artifacts/migration/fresh_db_outflow_request_replay_payload_v1.csv`
- `actual_outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv`
- `actual_outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
- `actual_outflow_partner_targeted_adapter` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv`
- `actual_outflow_partner_targeted_replay` `artifacts/migration/history_actual_outflow_partner_targeted_replay_payload_v1.csv`
- `actual_outflow_replay` `artifacts/migration/fresh_db_actual_outflow_replay_adapter_result_v1.json`
- `actual_outflow_replay` `artifacts/migration/fresh_db_actual_outflow_replay_payload_v1.csv`
- `outflow_request_line_replay` `artifacts/migration/fresh_db_outflow_request_line_replay_adapter_result_v1.json`
- `outflow_request_line_replay` `artifacts/migration/fresh_db_outflow_request_line_replay_payload_v1.csv`
- `actual_outflow_residual_replay` `artifacts/migration/fresh_db_actual_outflow_residual_replay_adapter_result_v1.json`
- `actual_outflow_residual_replay` `artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv`
- `actual_outflow_line_replay` `artifacts/migration/fresh_db_actual_outflow_line_replay_adapter_result_v1.json`
- `actual_outflow_line_replay` `artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv`
- `project_member_attachment_targeted_adapter` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv`
- `project_member_attachment_targeted_replay` `artifacts/migration/history_project_member_attachment_targeted_replay_adapter_result_v1.json`
- `project_member_attachment_targeted_replay` `artifacts/migration/history_project_member_attachment_targeted_replay_payload_v1.csv`
- `legacy_attachment_backfill_replay` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_adapter_result_v1.json`
- `legacy_attachment_backfill_replay` `artifacts/migration/fresh_db_legacy_attachment_backfill_replay_payload_v1.csv`
- `receipt_income_partner_targeted_adapter` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_payload_v1.csv`
- `receipt_income_partner_targeted_adapter` `artifacts/migration/fresh_db_legacy_receipt_income_replay_payload_v1.csv`
- `receipt_income_partner_targeted_adapter` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_payload_v1.csv`

## Runtime Output Promotion Backlog

- `manifest_dry_run` `artifacts/migration/fresh_db_replay_manifest_runner_dry_run_v1.md`
- `legacy_user_context_adapter` `artifacts/migration/fresh_db_legacy_user_context_replay_adapter_result_v1.json`
- `legacy_user_context_replay` `artifacts/migration/fresh_db_legacy_user_context_replay_write_result_v1.json`
- `legacy_user_project_scope_adapter` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json`
- `legacy_user_project_scope_adapter` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_payload_v1.csv`
- `legacy_user_project_scope_replay` `artifacts/migration/fresh_db_legacy_user_project_scope_replay_write_result_v1.json`
- `legacy_task_evidence_adapter` `artifacts/migration/fresh_db_legacy_task_evidence_replay_adapter_result_v1.json`
- `legacy_task_evidence_adapter` `artifacts/migration/fresh_db_legacy_task_evidence_replay_payload_v1.csv`
- `legacy_task_evidence_replay` `artifacts/migration/fresh_db_legacy_task_evidence_replay_write_result_v1.json`
- `legacy_attendance_checkin_adapter` `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json`
- `legacy_attendance_checkin_adapter` `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_payload_v1.csv`
- `legacy_attendance_checkin_replay` `artifacts/migration/fresh_db_legacy_attendance_checkin_replay_write_result_v1.json`
- `legacy_personnel_movement_adapter` `artifacts/migration/fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json`
- `legacy_personnel_movement_adapter` `artifacts/migration/fresh_db_legacy_personnel_movement_replay_payload_v1.csv`
- `legacy_personnel_movement_replay` `artifacts/migration/fresh_db_legacy_personnel_movement_replay_write_result_v1.json`
- `legacy_salary_line_adapter` `artifacts/migration/fresh_db_legacy_salary_line_replay_adapter_result_v1.json`
- `legacy_salary_line_replay` `artifacts/migration/fresh_db_legacy_salary_line_replay_write_result_v1.json`
- `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_rollback_targets_v1.csv`
- `partner_l4_anchor_completed` `artifacts/migration/fresh_db_partner_l4_replay_write_result_v1.json`
- `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_rollback_targets_v1.csv`
- `project_anchor_completed` `artifacts/migration/fresh_db_project_anchor_replay_write_result_v1.json`
- `legacy_account_master_adapter` `artifacts/migration/fresh_db_legacy_account_master_replay_adapter_result_v1.json`
- `legacy_account_master_replay` `artifacts/migration/fresh_db_legacy_account_master_replay_write_result_v1.json`
- `legacy_account_transaction_adapter` `artifacts/migration/fresh_db_legacy_account_transaction_replay_adapter_result_v1.json`
- `legacy_account_transaction_replay` `artifacts/migration/fresh_db_legacy_account_transaction_replay_write_result_v1.json`
- `legacy_material_catalog_adapter` `artifacts/migration/fresh_db_legacy_material_catalog_replay_adapter_result_v1.json`
- `legacy_material_catalog_replay` `artifacts/migration/fresh_db_legacy_material_catalog_replay_write_result_v1.json`
- `legacy_tender_registration_adapter` `artifacts/migration/fresh_db_legacy_tender_registration_replay_adapter_result_v1.json`
- `legacy_tender_registration_replay` `artifacts/migration/fresh_db_legacy_tender_registration_replay_write_result_v1.json`
- `legacy_material_stock_adapter` `artifacts/migration/fresh_db_legacy_material_stock_replay_adapter_result_v1.json`
- `legacy_material_stock_adapter` `artifacts/migration/fresh_db_legacy_material_stock_replay_payload_v1.csv`
- `legacy_material_stock_replay` `artifacts/migration/fresh_db_legacy_material_stock_replay_write_result_v1.json`
- `legacy_labor_subcontract_adapter` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_adapter_result_v1.json`
- `legacy_labor_subcontract_adapter` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_payload_v1.csv`
- `legacy_labor_subcontract_replay` `artifacts/migration/fresh_db_legacy_labor_subcontract_replay_write_result_v1.json`
- `legacy_equipment_lease_adapter` `artifacts/migration/fresh_db_legacy_equipment_lease_replay_adapter_result_v1.json`
- `legacy_equipment_lease_adapter` `artifacts/migration/fresh_db_legacy_equipment_lease_replay_payload_v1.csv`
- `legacy_equipment_lease_replay` `artifacts/migration/fresh_db_legacy_equipment_lease_replay_write_result_v1.json`
- `legacy_file_index_adapter` `artifacts/migration/fresh_db_legacy_file_index_replay_adapter_result_v1.json`
- `legacy_file_index_adapter` `artifacts/migration/fresh_db_legacy_file_index_replay_payload_v1.csv`
- `legacy_file_index_replay` `artifacts/migration/fresh_db_legacy_file_index_replay_write_result_v1.json`
- `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_rollback_targets_v1.csv`
- `contract_counterparty_partner_completed` `artifacts/migration/fresh_db_contract_counterparty_partner_replay_write_result_v1.json`
- `receipt_counterparty_partner_completed` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_rollback_targets_v1.csv`
- `receipt_counterparty_partner_completed` `artifacts/migration/fresh_db_receipt_counterparty_partner_replay_write_result_v1.json`
- `project_member_neutral_adapter` `artifacts/migration/_rollback_targets_v1.csv`
- `project_member_neutral_adapter` `artifacts/migration/fresh_db_project_member_neutral_replay_adapter_report_v1.md`
- `project_member_neutral_adapter` `artifacts/migration/fresh_db_project_member_neutral_replay_adapter_result_v1.json`
- `project_member_neutral_adapter` `artifacts/migration/fresh_db_project_member_neutral_replay_payload_v1.csv`
- `project_member_neutral_completed` `artifacts/migration/fresh_db_project_member_neutral_replay_rollback_targets_v1.csv`
- `project_member_neutral_completed` `artifacts/migration/fresh_db_project_member_neutral_replay_write_result_v1.json`
- `contract_header_remaining_adapter` `artifacts/migration/fresh_db_contract_remaining_adapter_report_v1.md`
- `contract_header_remaining_adapter` `artifacts/migration/fresh_db_contract_remaining_adapter_result_v1.json`
- `contract_header_remaining_adapter` `artifacts/migration/fresh_db_contract_remaining_replay_payload_v1.csv`
- `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_post_write_snapshot_v1.csv`
- `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_pre_write_snapshot_v1.csv`
- `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_rollback_targets_v1.csv`
- `contract_header_completed_1332` `artifacts/migration/fresh_db_contract_remaining_write_result_v1.json`
- `contract_missing_partner_anchors` `artifacts/migration/fresh_db_contract_missing_partner_anchor_rollback_targets_v1.csv`
- `contract_missing_partner_anchors` `artifacts/migration/fresh_db_contract_missing_partner_anchor_write_report_v1.md`
- `contract_missing_partner_anchors` `artifacts/migration/fresh_db_contract_missing_partner_anchor_write_result_v1.json`
- `contract_12_missing_partner_anchors` `artifacts/migration/contract_12_row_missing_partner_anchor_rollback_targets_v1.csv`
- `contract_12_missing_partner_anchors` `artifacts/migration/contract_12_row_missing_partner_anchor_write_result_v1.json`
- `contract_header_special_12` `artifacts/migration/contract_12_row_post_write_snapshot_v1.csv`
- `contract_header_special_12` `artifacts/migration/contract_12_row_pre_write_snapshot_v1.csv`
- `contract_header_retry_57` `artifacts/migration/fresh_db_contract_57_retry_post_write_snapshot_v1.csv`
- `contract_header_retry_57` `artifacts/migration/fresh_db_contract_57_retry_pre_write_snapshot_v1.csv`
- `contract_header_retry_57` `artifacts/migration/fresh_db_contract_57_retry_rollback_targets_v1.csv`
- `contract_header_retry_57` `artifacts/migration/fresh_db_contract_57_retry_write_result_v1.json`
- `contract_unreached_ready_adapter` `artifacts/migration/history_contract_unreached_ready_replay_adapter_result_v1.json`
- `contract_unreached_ready_adapter` `artifacts/migration/history_contract_unreached_ready_replay_payload_v1.csv`
- `contract_unreached_ready_replay` `artifacts/migration/history_contract_unreached_ready_replay_rollback_targets_v1.csv`
- `contract_unreached_ready_replay` `artifacts/migration/history_contract_unreached_ready_replay_write_result_v1.json`
- `partner_master_targeted_adapter` `artifacts/migration/history_partner_master_targeted_replay_adapter_result_v1.json`
- `partner_master_targeted_adapter` `artifacts/migration/history_partner_master_targeted_replay_payload_v1.csv`
- `partner_master_targeted_replay` `artifacts/migration/history_partner_master_targeted_replay_rollback_targets_v1.csv`
- `partner_master_targeted_replay` `artifacts/migration/history_partner_master_targeted_replay_write_result_v1.json`
- `contract_partner_recovery_adapter` `artifacts/migration/history_contract_partner_recovery_adapter_result_v1.json`
- `contract_partner_recovery_adapter` `artifacts/migration/history_contract_partner_recovery_payload_v1.csv`
- `contract_partner_recovery_replay` `artifacts/migration/history_contract_partner_recovery_rollback_targets_v1.csv`

## Decision

`gap report is informational until a release package is fetched; release-package verification remains the blocking gate`
