# Project Dry Run Report v2

## Result

PASS

## Scope

- Task: `ITER-2026-04-13-1820`
- Input sample: `data/migration_samples/project_sample_v1.csv`
- Result artifact: `artifacts/migration/project_dry_run_result_v1.json`
- Importer: `scripts/migration/project_dry_run_importer.py`

The importer is dry-run only. It does not connect to Odoo, call ORM, or write a
database.

## Dry-Run Summary

| Metric | Value |
| --- | ---: |
| sample rows | 30 |
| safe fields | 22 |
| create | 30 |
| update | 0 |
| error rows | 0 |
| header errors | 0 |

`update=0` because this dry-run intentionally does not call ORM and no
`existing-identities` file was provided. Update logic exists in the dry-run
importer and is driven only by an optional `legacy_project_id` identity file.

## Validation Checks

- Header contains only the 22 safe-slice fields.
- Required fields `legacy_project_id` and `name` are present for 30/30 rows.
- No duplicate `legacy_project_id` exists in the sample.
- No forbidden fields are present in the sample.
- No database or ORM access is used.

## Risks

- Existing-record update distribution cannot be proven without a separate
  exported identity file because ORM/DB calls are forbidden in this batch.
- The sample includes unresolved branch company names, but they remain raw
  legacy fields only.
- The sample includes unresolved specialty labels, but they remain raw legacy
  fields only.
- One `PROJECT_ENV=测试项目` warning case is included; later write-mode sample
  selection should explicitly decide whether to exclude it.
- Three rows lack `other_system_id`; this is non-blocking because
  `legacy_project_id` is the primary key.

## Artifact

The machine-readable dry-run result is in
`artifacts/migration/project_dry_run_result_v1.json`.
