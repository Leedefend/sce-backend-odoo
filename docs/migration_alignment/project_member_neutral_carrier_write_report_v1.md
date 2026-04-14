# Project member neutral carrier write report v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030N`  
Database: `sc_demo`

## Input

- Safe slice: `artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv`
- Rows: 34

## Write Target

```text
sc.project.member.staging
```

Forbidden target:

```text
project.responsibility
```

## Result

| Item | Result |
| --- | ---: |
| created | 34 |
| updated | 0 |
| project.responsibility writes | 0 |
| rollback target rows | 34 |
| matched neutral records | 34 |
| rollback eligible rows | 34 |
| visibility changed | false |

## Visibility Review

The write script captured project visibility before and after the neutral
carrier write for the safe-slice users and projects.

Result:

```text
visibility_changed = false
```

The post-write readonly review also confirmed that the same project/user pairs
were not written to `project.responsibility`.

## Rollback

Rollback target:

```text
artifacts/migration/project_member_rollback_targets_v1.csv
```

Rollback must delete only `sc.project.member.staging` rows for:

```text
import_batch = ITER-2026-04-14-0030N
neutral_id in rollback target list
```

No rollback against `project.responsibility` is needed because this batch did
not write that model.
