# Project Create-Only Write Trial Report v1

## Result

PASS

## Scope

- Task: `ITER-2026-04-13-1825`
- Target database: `sc_demo`
- Target model: `project.project`
- Input sample: `artifacts/migration/project_sample_v1.csv`
- Write script: `scripts/migration/project_create_only_write_trial.py`
- Write result: `artifacts/migration/project_create_only_write_result_v1.json`

This batch executed the explicitly authorized 30-row create-only write trial. It
did not run update/upsert logic and did not import full legacy data.

## Pre-Write Gate

| Check | Result |
| --- | ---: |
| sample rows | 30 |
| safe fields | 22 |
| pre-write target matches | 0 |
| pre-write dry-run create | 30 |
| pre-write dry-run update | 0 |
| pre-write dry-run errors | 0 |

Pre-write artifacts:

- `artifacts/migration/project_existing_identity_snapshot_pre_write_v1.csv`
- `artifacts/migration/project_dry_run_pre_write_result_v1.json`
- `artifacts/migration/project_create_only_pre_write_snapshot_v1.csv`

## Write Result

| Metric | Value |
| --- | ---: |
| created | 30 |
| updated | 0 |
| errors | 0 |
| post-write identity count | 30 |

Post-write artifact:

- `artifacts/migration/project_create_only_post_write_snapshot_v1.csv`

## Post-Write Verification

A read-only Odoo shell check confirmed:

| Metric | Value |
| --- | ---: |
| sample identities | 30 |
| records found | 30 |
| unique identities found | 30 |
| missing identities | 0 |
| duplicate identities | 0 |

`make verify.native.business_fact.static` also passed.

## Written Field Boundary

The write script writes only non-empty values from the 22 approved safe-slice
fields. It does not write:

- `company_id`
- `project_type_id`
- `project_category_id`
- `stage_id`
- `lifecycle_state`
- `active`
- user relation fields
- partner relation fields
- contract, payment, supplier, tax, bank, account, cost, settlement, or
  attachment records
- official `project_code` from legacy `PROJECT_CODE`

## Risks

- This is still a 30-row sample trial, not full import readiness.
- Update/upsert remains unapproved because target identity rows were 0 before
  the trial.
- Company, specialty, lifecycle/state, user, and partner mappings remain raw
  safe-slice fields only.
- Rollback, if needed, must use only the 30 sample `legacy_project_id` values
  captured in the result artifacts.

## Conclusion

The 30-row create-only project skeleton write trial into `sc_demo` passed. The
next safe step is post-write functional review and rollback rehearsal planning,
not full import.
