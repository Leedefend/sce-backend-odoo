# Project Dry Run Update Path Report v1

## Result

PASS

## Scope

- Task: `ITER-2026-04-13-1821`
- Input sample: `data/migration_samples/project_sample_v1.csv`
- Existing identity snapshot: `data/migration_samples/project_existing_identity_snapshot_v1.csv`
- Result artifact: `artifacts/migration/project_dry_run_update_path_result_v1.json`
- Importer: `scripts/migration/project_dry_run_importer.py`

This run is still dry-run only. It does not connect to Odoo, call ORM, write a
database, or import full legacy data.

## Identity Snapshot

The snapshot contains 10 `legacy_project_id` values selected from the 30-row
safe-slice sample. It is an external simulation file, not a database export from
Odoo.

| Metric | Value |
| --- | ---: |
| snapshot rows | 10 |
| unique `legacy_project_id` values | 10 |
| missing from sample | 0 |

## Dry-Run Summary

| Metric | Value |
| --- | ---: |
| sample rows | 30 |
| safe fields | 22 |
| create | 20 |
| update | 10 |
| error rows | 0 |
| header errors | 0 |

The update path is driven only by `legacy_project_id`, consistent with
`project_import_identity_policy_v1.md`.

## Validation Checks

- Header contains only the 22 safe-slice fields.
- Required fields `legacy_project_id` and `name` remain present for 30/30 rows.
- No duplicate `legacy_project_id` exists in the input sample.
- The identity snapshot has 10 unique IDs and all 10 appear in the sample.
- No database or ORM access is used.

## Remaining Risks

- The identity snapshot is simulated from the sample. Before write-mode import,
  it should be replaced by a controlled export of existing project identities.
- This run validates classification, not Odoo write constraints or record rule
  behavior.
- Company, specialty, state, user, and partner values remain raw safe-slice
  fields only and are not formally mapped to Many2one records.
- The previous sample warning still applies: one sampled row carries test-project
  semantics and three rows lack `other_system_id`.

## Conclusion

The no-write create/update classification logic is usable for the next
non-write rehearsal stage. It is still not sufficient for database write-mode
import.
