# Migration Assets

The migration asset payloads are externalized and are no longer tracked in Git.

Materialize the locked package before running migration asset verification or
history replay:

```bash
make migration.assets.fetch
make migration.assets.verify_all
```

By default the lock records the locally generated package path used during this
cleanup. In another environment, set one of:

```bash
MIGRATION_ASSET_PACKAGE_PATH=/path/to/migration_assets_release_*.tar.gz
MIGRATION_ASSET_PACKAGE_URL=https://private-authenticated-object-store/...
```

Do not publish migration asset packages to public GitHub Releases. They contain
reconstructed user and business migration data.

The package hash is pinned in
`docs/migration_alignment/migration_asset_package_lock_v1.json`.
