# Project Create-Only Expansion Rollback Dry-Run v1

Status: ROLLBACK_READY  
Iteration: ITER-2026-04-13-1836

## 1. Rollback Target

Rollback target file:

```text
artifacts/migration/project_create_only_expand_post_write_snapshot_v1.csv
```

Rollback key:

```text
legacy_project_id
```

## 2. Dry-Run Result

| Item | Result |
| --- | ---: |
| total targets | 100 |
| matched rows | 100 |
| missing rows | 0 |
| duplicate matches | 0 |
| out-of-scope matches | 0 |
| projection mismatches | 0 |

## 3. Real Rollback Status

This batch did not delete anything.

Real rollback is technically lockable by the 100 `legacy_project_id` values, but
still requires a separate explicit delete authorization batch.

## 4. Delete Safety Rules For Future Batch

- Delete only records matched by the 100 `legacy_project_id` values.
- Do not delete by project name, company text, stage, date, or source row order.
- Re-run this dry-run immediately before delete.
- Stop if any duplicate, missing, out-of-scope, or projection mismatch appears.

