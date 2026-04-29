# Migration Asset Delivery Audit v1

Status: `PASS_WITH_PACKAGING_ACTIONS`

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
