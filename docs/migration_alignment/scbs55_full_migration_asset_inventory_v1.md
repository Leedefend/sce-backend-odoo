# SCBS55 Full Migration Asset Inventory v1

Status: `PASS`

## Scope

- freeze: `docs/migration_alignment/scbs55_full_migration_asset_freeze_v1.json`
- package: `migration_assets_release_20260429T135959Z_baseline`
- materializes: `migration_assets/ and artifacts/migration/`
- 42-surface evidence: `artifacts/migration/scbs55_wutao_old_new_final_aligned_compare.json`

## Runtime Artifacts

- files: `225`
- total size MB: `224.76`

### By Category

- `adapter_result`: `6`
- `browser_screenshot`: `6`
- `comparison_evidence`: `14`
- `old_live_identity_dump`: `42`
- `old_live_row_dump`: `62`
- `other_artifact`: `8`
- `probe_evidence`: `44`
- `replay_payload`: `19`
- `visible_surface_export`: `12`
- `write_result`: `12`

### Largest Files

- `artifacts/migration/BGGL_TZXX_document_borrow_visible.tsv`: `49.58 MB`
- `artifacts/migration/scbs55_old_pages_locked_runtime/supplier_contract.json`: `19.17 MB`
- `artifacts/migration/fresh_db_legacy_account_transaction_replay_payload_v1.csv`: `17.01 MB`
- `artifacts/migration/scbs_visible_artifacts_20260529.tgz`: `16.51 MB`
- `artifacts/migration/fresh_db_legacy_payment_residual_replay_payload_v1.csv`: `12.36 MB`
- `artifacts/migration/scbs55_old_pages_locked_runtime/engineering_progress_receipt.json`: `8.91 MB`
- `artifacts/migration/fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv`: `6.75 MB`
- `artifacts/migration/fresh_db_legacy_income_invoice_replay_payload_v1.csv`: `6.11 MB`
- `artifacts/migration/scbs_55_old_live_full_rows_seq042_进项上报.json.gz`: `5.61 MB`
- `artifacts/migration/scbs55_old_pages_locked_runtime/self_funding_income.json`: `5.48 MB`

## User Visible Surface Evidence

- exists: `True`
- status: `PASS`
- checked count: `42`
- blocking count: `0`
- total old rows: `142427`
- total new rows: `142427`

## History Continuity Replay

- script: `scripts/migration/history_continuity_oneclick.sh`
- steps: `221`

### Step Kinds

- `adapter`: `69`
- `formal_projection`: `42`
- `normalization`: `6`
- `other`: `18`
- `probe`: `16`
- `write_replay`: `70`

## Ungoverned Runtime Scripts

- `frontend/apps/web/scripts/user_list_field_data_coverage.cjs`: `reference_only_not_delivery_asset`
- `scripts/migration/scbs55_live_delta_backfill_write.py`: `reference_only_not_delivery_asset`
