# Migration Asset Drift Inventory (2026-07-15)

This static inventory was produced at code baseline `5c41a434c` without legacy-system access, database access, replay, lock refresh, or historical-baseline creation.

The one-click chain contains 221 steps: 69 adapters, 62 baseline replay steps, 42 formal projections, 23 repair/normalization steps, 20 probes/guards, and 5 special steps. Its SHA256 is `980daf94887576ace80744ac221ad723b25eaf2db17f295358fb2fd0d2c64bfa`.

Static inspection found 127 write scripts. Twenty-two do not directly contain the known stable source-key terms and require individual idempotency review. Forty-two contain unlink, SQL delete, cleanup, or rebuild-related text; these are isolated-rehearsal review candidates, not evidence that records should be deleted.

The current lock names `migration_assets_release_20260618T104314Z`, SHA256 `b8ba1f85cf084679655015b8d5f763b47c8d7c964e1e9920ca2f3fb1e76b84f0`, 634,798,244 bytes, and 3,723 files, but package and checksum paths are empty and the archive is not materialized. The working `migration_assets/` tree contains 99 files and 490,713,632 bytes.

`make migration.assets.full_scope_guard` fails with 13 independently reported drifts covering package identity/SHA/size/materialization, asset counts/size, 221-versus-219 replay steps, and delivery/release required artifact sets. The gap report remains `PASS_WITH_GAPS`; the full freeze remains `topic_in_progress`.

`scbs55_live_delta_backfill_write.py` remains classified as `reference_only_not_delivery_asset`, has no watermark/checkpoint, and is not a continuous synchronization entrypoint.

```text
MIGRATION_ASSET_DRIFT_INVENTORIED=true
MIGRATION_ASSET_LOCK_REFRESHED=false
REPLAY_EXECUTED=false
HISTORICAL_BASELINE_CREATED=false
```

Chinese: [migration_asset_drift_inventory_20260715.md](migration_asset_drift_inventory_20260715.md)
