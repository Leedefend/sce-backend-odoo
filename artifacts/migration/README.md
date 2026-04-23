# Migration Rebuild Assets

This directory is intentionally tracked.

It contains the migration/rebuild assets required to reproduce legacy business
data reconstruction on a fresh server checkout:

- replay manifests and adapter plans
- write payloads and authorization packets
- pre-write and post-write snapshots
- rollback target lists
- validation results and check logs
- migration evidence used by `docs/migration_alignment/**` and task result
  records

The parent `artifacts/` directory remains ignored by default. Only
`artifacts/migration/**` is unignored because these files are part of the
business-data rebuild handoff, not disposable local runtime output.

Do not place runtime databases, Redis dumps, logs unrelated to migration
validation, frontend build output, or local configuration in this directory.
