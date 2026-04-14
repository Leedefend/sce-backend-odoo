# Project Dry Run Target Identity Report v1

## Result

PASS

## Scope

- Task: `ITER-2026-04-13-1823`
- Target database: `sc_demo`
- Input sample: `data/migration_samples/project_sample_v1.csv`
- Target identity snapshot: `data/migration_samples/project_existing_identity_snapshot_target_v1.csv`
- Result artifact: `artifacts/migration/project_dry_run_target_identity_result_v1.json`
- Importer: `scripts/migration/project_dry_run_importer.py`

This run did not write database records and did not import legacy project data.
The target-environment access was limited to a read-only identity snapshot
export through the Makefile `odoo.shell.exec` entry.

## Target Identity Snapshot

The read-only export inspected `project.project` in `sc_demo` for these identity
fields:

- `legacy_project_id`
- `other_system_id`
- `other_system_code`

| Metric | Value |
| --- | ---: |
| target identity rows | 0 |
| exported fields | 3 |
| snapshot file | `data/migration_samples/project_existing_identity_snapshot_target_v1.csv` |

The target database currently has no `project.project` records with
`legacy_project_id` populated. Therefore this rehearsal cannot produce update
classification from target identities.

## Dry-Run Summary

| Metric | Value |
| --- | ---: |
| sample rows | 30 |
| safe fields | 22 |
| create | 30 |
| update | 0 |
| error rows | 0 |
| header errors | 0 |

## Validation Checks

- The target identity snapshot was exported through `ENV=dev DB_NAME=sc_demo make odoo.shell.exec`.
- The exporter wrote to `/mnt/artifacts/...`, a writable mounted artifact path.
- The snapshot was copied to `data/migration_samples/project_existing_identity_snapshot_target_v1.csv`.
- The dry-run importer used only the safe-slice sample and the exported identity snapshot.
- Result JSON is parseable.
- No database write operation was executed.

## Risks

- Since the target identity snapshot has 0 rows, update classification remains
  covered by the simulated 1821 run but not by target-environment data.
- If the target database is expected to already contain migrated project
  skeletons, the missing `legacy_project_id` values are a readiness blocker for
  upsert-style import.
- If the target database is intentionally empty for project migration, the
  create-only result is expected and not blocking for a first skeleton create
  rehearsal.
- This run still does not validate write-mode ORM constraints, permissions,
  transactions, or rollback behavior.

## Conclusion

The target-identity no-write rehearsal is technically successful. It supports a
create-only first skeleton import rehearsal for `sc_demo`, but it does not prove
target-data update behavior because the target identity snapshot is empty.
