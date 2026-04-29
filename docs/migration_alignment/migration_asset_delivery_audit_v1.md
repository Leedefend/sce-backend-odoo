# Migration Asset Delivery Audit v1

Status: `PASS_WITH_PACKAGING_ACTIONS`

## Scope

Read-only audit for production delivery packaging. This report does not
connect to Odoo, execute replay writes, or mutate migration assets.

## Summary

- catalog packages: `23`
- asset files: `98`
- referenced files: `93`
- unreferenced files: `5`
- total asset size MB: `467.27`
- replay steps: `144`
- duplicate materialized parts: `1`

## Decision

- blockers: `0`
- packaging actions: `2`

### Packaging Actions

- remove duplicated materialized XML or parts from the final release package after choosing one canonical form
- classify unreferenced migration asset files as delivery evidence or remove from release package

## Entrypoints

- `history.continuity.rehearse`: `True`
- `history.continuity.replay`: `True`
- `history.production.fresh_init`: `True`
- production calls one-click replay: `True`
- `HISTORY_CONTINUITY_START_AT`: `True`

## Duplicate Materialized Parts

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml` (120.01 MB) and `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts` (3 parts, 120.01 MB)

## Unreferenced Asset Files

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-000.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-001.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-002.part`
- `migration_assets/manifest/migration_asset_coverage_snapshot_v1.json`
- `migration_assets/manifest/receipt_blocker_policy_snapshot_v1.json`

## Large Files

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml`: `120.01 MB`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-000.part`: `60.0 MB`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-001.part`: `60.0 MB`
- `migration_assets/manifest/legacy_workflow_audit_external_id_manifest_v1.json`: `31.06 MB`
- `migration_assets/20_business/outflow_request_line/outflow_request_line_v1.xml`: `18.34 MB`
- `migration_assets/30_relation/project_member/project_member_neutral_v1.xml`: `16.82 MB`
- `migration_assets/30_relation/legacy_attachment_backfill/legacy_attachment_backfill_v1.xml`: `14.52 MB`
- `migration_assets/30_relation/legacy_expense_deposit/legacy_expense_deposit_v1.xml`: `13.18 MB`
- `migration_assets/20_business/actual_outflow/actual_outflow_core_v1.xml`: `10.05 MB`

## Output

- JSON: `artifacts/migration/migration_asset_delivery_audit_v1.json`
- Git policy: generated audit JSON stays local and must not be committed.
