# Migration Asset Delivery Audit v1

Status: `PASS_WITH_PACKAGING_ACTIONS`

## Scope

Read-only audit for production delivery packaging. This report does not
connect to Odoo, execute replay writes, or mutate migration assets.

## Summary

- catalog packages: `23`
- asset files: `97`
- referenced files: `93`
- unreferenced files: `4`
- total asset size MB: `324.69`
- replay steps: `219`
- required replay artifacts: `106`
- missing required replay artifacts: `0`
- mandatory business scopes: `1`
- missing business-scope artifacts: `0`
- duplicate materialized parts: `0`

## Decision

- blockers: `0`
- packaging actions: `1`

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

- `migration_assets/10_master/project/user_project_master_review_decisions_20260521.csv`
- `migration_assets/10_master/project/user_project_name_strategy_20260520.csv`
- `migration_assets/manifest/migration_asset_coverage_snapshot_v1.json`
- `migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json`

## Large Files

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml`: `109.62 MB`
- `migration_assets/manifest/legacy_workflow_audit_external_id_manifest_v1.json`: `28.39 MB`
- `migration_assets/20_business/outflow_request_line/outflow_request_line_v1.xml`: `18.34 MB`
- `migration_assets/30_relation/project_member/project_member_neutral_v1.xml`: `16.82 MB`
- `migration_assets/30_relation/legacy_attachment_backfill/legacy_attachment_backfill_v1.xml`: `14.52 MB`
- `migration_assets/30_relation/legacy_expense_deposit/legacy_expense_deposit_v1.xml`: `13.18 MB`
- `migration_assets/20_business/actual_outflow/actual_outflow_core_v1.xml`: `10.05 MB`

## Output

- JSON: `artifacts/migration/migration_asset_delivery_audit_v1.json`
