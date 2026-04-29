# Migration Asset Release Package v1

Status: `PASS`

- package_id: `migration_assets_release_20260429T120811Z`
- package_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260429T120811Z.tar.gz`
- package_url: `https://github.com/Leedefend/sce-backend-odoo/releases/download/migration-assets-20260429T120811Z/migration_assets_release_20260429T120811Z.tar.gz`
- sha256_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260429T120811Z.tar.gz.sha256`
- sha256: `b9498cbbf605527b13e84d8f7710eca0454f3c7b065e990db728e1d70b699d91`
- package_size_mb: `37.51`
- included_file_count: `95`
- excluded_file_count: `3`
- payload_mode: `packaged_artifacts`

## Repository Policy

- `migration_assets` payload files are externalized and are not tracked in Git.
- The locked package is recorded in `docs/migration_alignment/migration_asset_package_lock_v1.json`.
- The canonical external package is published as GitHub Release `migration-assets-20260429T120811Z`.
- Before verification or replay, materialize the package with `make migration.assets.fetch`.

## Excluded Paths

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-000.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-001.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-002.part`

## Verification

- Excluded `.xml.parts` files are not packaged.
- `artifacts/migration` replay payloads are packaged for old-DB-free production replay.
