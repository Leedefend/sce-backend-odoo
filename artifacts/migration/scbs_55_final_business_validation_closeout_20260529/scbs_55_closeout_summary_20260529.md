# SCBS55 Closeout Summary 2026-05-29

Database: `sc_odoo`

## Final Status

- SCBS55 user-visible surface closeout is complete locally.
- Old/new browser surface compare: PASS, 55/55 rows, 0 failures.
- Strict old/new historical visible-field reconciliation: PASS, 42/42 list-backed entries, 0 blocking rows. `奖金` remains the only allowed legacy-empty entry.
- Post-reconciliation browser list acceptance: PASS, 42/42 list-backed entries, 0 failures, 0 fatal console errors.
- List closure probe: PASS, 55/55 rows, 0 failures.
- Form operability probe: PASS, 55/55 rows, 0 failures, 1 warning.
- Runtime list strict probe: PASS, 55/55 rows, 0 failures.
- Action list alias views: PASS, 42/42 list-backed entries; 13 report/dashboard/non-list entries intentionally have no list contract.
- Action form contracts: PASS, 42/42 list-backed entries; 13 skipped for empty list contract.
- Module upgrade completed after fixing the company currency bootstrap blocker.

## Server Legacy DB Recovery

The remaining zero-data surfaces were completed from the server legacy SQL Server restore:

- Host: `sc-root`
- Container: `legacy-mssql-restore`
- Database: `LegacyDb`
- Backup path observed on server: `/opt/sce-upgrade-assets/20260527/legacy_mssql/DB_Build_SC_BS_20260413044808.bak`

Generated server payloads were copied back into this closeout artifact set and replayed/projected into local `sc_odoo`.

## Recovered Data

- Residual business facts from server old DB: 3 tables, 2079 total rows, 2060 active rows.
- `请假/休假审批单`: 347 projected rows, 339 delivered active rows.
- `印章使用审批表`: 1565 projected/delivered rows.
- `社保人员登记`: 167 projected rows, 156 delivered active rows.
- `投标报名费申请`: 122 input rows, 115 active/projected rows.
- `借款申请`: 37 rows from `BGGL_JHK_JKSQ`.
- `还款登记`: 24 rows from `BGGL_JHK_HKDJ`.
- `扣款单`: 137 rows updated idempotently from `C_ZFSQGL_KKD`.
- `项目还公司款登记`: 98 rows updated idempotently from `ZJGL_ZJSZ_DKGL_HKDJ`.

## List Closure Totals

- Row count: 55
- List contract count: 42
- Non-list/report/dashboard skips: 13
- Failures: 0
- Zero rows: 1 allowed legacy-empty row, `奖金` (`BGGL_XZ_JJ`/`BGGL_XZ_JJ_CB` source tables contain 0 rows)

## Historical Data Alignment

- Scope: all 42 list-backed user-visible entries from the 55-entry SCBS set.
- Exclusion: `奖金`, because the legacy source tables contain 0 rows and the user explicitly allowed bonus data to be ignored.
- Method: strict key-based full-field reconciliation against the legacy visible CSV/TSV payloads copied from the server restored old database.
- Result: PASS, blocking_count=0, pass_count=42, required_entry_count=42.
- Backfill mechanism: sidecar table `sc_p1_legacy_visible_alias_payload` stores authoritative legacy visible values by `(model, res_id)`; user-visible alias fields read this payload before falling back to business fields.
- Browser check after Odoo restart: PASS, checked_count=42, pass_count=42, fail_count=0.

## Artifact Pointers

- `artifacts/browser/scbs55-old-new-surface-compare/20260528T230427/summary.json`
- `artifacts/browser/scbs55-old-new-surface-compare/20260528T230427/report.md`
- `artifacts/browser/scbs55-user-visible-list/20260528T234554/summary.json`
- `artifacts/browser/scbs55-user-visible-list/20260528T234554/report.md`
- `artifacts/migration/scbs_55_historical_reconcile_20260529_readonly_final/scbs_55_legacy_visible_field_full_reconcile_probe_result_v1.json`
- `artifacts/migration/scbs_55_historical_reconcile_20260529_readonly_final/scbs_55_legacy_visible_field_full_reconcile_probe_report_v1.md`
- `artifacts/migration/scbs_55_historical_reconcile_20260529_write/scbs_55_legacy_visible_field_full_reconcile_probe_result_v1.json`
- `artifacts/browser/scbs55-user-visible-list/20260528T224827/summary.json`
- `scbs_55_user_visible_list_closure_probe_result_v1.json`
- `scbs_55_user_visible_list_closure_probe_report_v1.md`
- `scbs_55_user_visible_form_operability_probe_result_v1.json`
- `scbs_55_user_visible_form_operability_probe_report_v1.md`
- `scbs_55_user_visible_runtime_list_strict_probe_result_v1.json`
- `scbs_55_user_visible_runtime_list_strict_probe_report_v1.md`
- `fresh_db_legacy_business_fact_residual_replay_adapter_result_v1.json`
- `fresh_db_legacy_business_fact_residual_replay_write_result_v1.json`
- `fresh_db_legacy_tender_doc_purchase_projection_write_result_v1.json`
- `fresh_db_scbs55_remaining_finance_projection_write_result_v1.json`
