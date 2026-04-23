# Project Create-Only Expansion Rollback Lock v1

Status: Locked By Legacy Identity  
Iteration: ITER-2026-04-13-1835

## 1. Rollback Key

Rollback key: `legacy_project_id`

Rollback must target only the 100 values present in:

```text
artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv
```

Rollback must not use project name, company text, stage, date, or row order.

## 2. Lock Result

| Item | Result |
| --- | ---: |
| target rows | 100 |
| matched rows after write | 100 |
| duplicate legacy_project_id | 0 |
| missing legacy_project_id | 0 |
| projection mismatches | 0 |

## 3. Real Rollback Status

Real delete is not authorized in this batch.

Before any real rollback, open a dedicated rollback authorization batch that:

- reads the post-write snapshot;
- dry-runs all 100 `legacy_project_id` values;
- confirms no out-of-scope match;
- confirms no duplicate match;
- deletes only after explicit delete authorization.

