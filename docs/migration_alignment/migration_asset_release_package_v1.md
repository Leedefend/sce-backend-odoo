# Migration Asset Release Package v1

Status: `PASS`

- package_id: `migration_assets_release_20260513T030706Z`
- package_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260513T030706Z.tar.gz`
- sha256_path: `/tmp/sce_migration_asset_release/migration_assets_release_20260513T030706Z.tar.gz.sha256`
- sha256: `833d4ba0cf9352e67618d3ff06ad6099d4241ed9bfe42c2bf352eae5f14b2789`
- package_size_mb: `329.57`
- included_file_count: `2560`
- excluded_file_count: `0`
- payload_mode: `packaged_artifacts`
- deployment_entrypoint: `scripts/migration/history_continuity_oneclick.sh`

## Excluded Paths

- none

## Verification

- Excluded `.xml.parts` files are not packaged.
- `artifacts/migration` replay payloads are packaged for old-DB-free production replay.
- Replay entrypoint, migration Python scripts, and migration shell scripts are packaged with the assets.
- Verify the package with `MIGRATION_ASSET_RELEASE_PACKAGE=<package_path> make migration.assets.release_package.verify`.
- Verify after extraction with `python3 scripts/migration/migration_asset_bus.py --asset-root migration_assets --catalog migration_assets/manifest/migration_asset_catalog_v1.json --verify-only --check`.
- Verify packaged replay scope with `python3 scripts/migration/migration_asset_delivery_audit.py --asset-root migration_assets`.
- Rehearse against a fresh target DB with `HISTORY_CONTINUITY_MODE=rehearse HISTORY_CONTINUITY_USE_PACKAGED_PAYLOADS=1 DB_NAME=<target_db> MIGRATION_REPLAY_DB_ALLOWLIST=<target_db> bash scripts/migration/history_continuity_oneclick.sh`.
