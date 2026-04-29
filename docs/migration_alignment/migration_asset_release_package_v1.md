# Migration Asset Release Package v1

Status: `PASS`

- package_id: `migration_assets_release_20260428T170353Z`
- package_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260428T170353Z.tar.gz`
- sha256_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260428T170353Z.tar.gz.sha256`
- sha256: `1c4e51320990ed6847aa6d8bea21d39de594806776944bd3d32800496bf57813`
- package_size_mb: `237.62`
- included_file_count: `776`
- excluded_file_count: `3`
- payload_mode: `packaged_artifacts`

## Excluded Paths

- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-000.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-001.part`
- `migration_assets/30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml.parts/part-002.part`

## Verification

- Excluded `.xml.parts` files are not packaged.
- `artifacts/migration` replay payloads are packaged for old-DB-free production replay.
- Generated package JSON and replay payloads are local artifacts and must not be committed to Git.
