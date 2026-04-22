# Legacy Attachment Backfill Asset Package v1

Status: frozen checkpoint

## Scope

This checkpoint backfills URL-type `ir.attachment` XML assets for deterministic
attachment links found before the receipt invoice attachment lane.

No binary file content is copied into the repository and no target database
business data is imported in this batch.

## Package

- asset package: `legacy_attachment_backfill_sc_v1`
- source table: `BASE_SYSTEM_FILE`
- target model: `ir.attachment`
- XML: `migration_assets/30_relation/legacy_attachment_backfill/legacy_attachment_backfill_v1.xml`
- asset manifest: `migration_assets/manifest/legacy_attachment_backfill_asset_manifest_v1.json`
- external-id manifest: `migration_assets/manifest/legacy_attachment_backfill_external_id_manifest_v1.json`
- validation manifest: `migration_assets/manifest/legacy_attachment_backfill_validation_manifest_v1.json`

## Result

- URL attachment records: `18458`
- matched target business records: `18456`
- DB writes: `0`
- Odoo shell: `false`

Lane counts:

- `project`: `464`
- `project_member`: `7860`
- `actual_outflow`: `5443`
- `supplier_contract`: `1`
- `supplier_contract_line`: `1`
- `outflow_request_line`: `4689`

## Boundary

Included:

- URL-type `ir.attachment` metadata
- explicit `res_model`
- `res_id` by target external ID
- legacy file ID, MD5, and size in manifest evidence

Excluded:

- `datas`
- `raw`
- `db_datas`
- `store_fname`
- binary file custody
- file copy into repository

## Verification

Passed commands:

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-15-MIGRATION-ATTACHMENT-BACKFILL-ASSET-PACKAGE.yaml`
- `python3 -m py_compile scripts/migration/legacy_attachment_backfill_asset_generator.py scripts/migration/legacy_attachment_backfill_asset_verify.py scripts/migration/migration_asset_bus.py scripts/migration/migration_asset_catalog_verify.py scripts/migration/migration_asset_coverage_snapshot.py`
- `python3 scripts/migration/legacy_attachment_backfill_asset_generator.py --asset-root migration_assets --expected-ready 18458 --check`
- `python3 scripts/migration/legacy_attachment_backfill_asset_verify.py --asset-root migration_assets --lane legacy_attachment_backfill --check`
- `python3 scripts/migration/migration_asset_catalog_verify.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check`
- `python3 scripts/migration/migration_asset_coverage_snapshot.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --check`
- `git diff --check`

## Coverage

The migration asset catalog now contains `17` packages with `112434` loadable
records and `8398` blocked/discarded records.

## Rebuild Note

This package lets a fresh Odoo database rebuild attachment records and business
object links for prior migrated facts. File bytes still require an external
file-custody plan.
