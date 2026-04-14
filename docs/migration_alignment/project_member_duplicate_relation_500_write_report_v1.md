# Project member duplicate-relation 500-row write report v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030NZ`  
Database: `sc_demo`

## Target

```text
sc.project.member.staging
```

This write stores duplicate-relation evidence only. It does not write
`project.responsibility`.

## Result

| Item | Count |
| --- | ---: |
| created | 500 |
| updated | 0 |
| rollback target rows | 500 |
| project.responsibility writes | 0 |
| visibility changed | false |

## Boundary

The written rows keep `role_fact_status = missing`.

They are historical evidence rows for multiple legacy records that map to the
same `project_id/user_id` relation. They must not be interpreted as:

- responsibility roles;
- project visibility rules;
- approval facts;
- owner or reviewer facts;
- workflow routing facts.

## Rollback

Rollback target:

```text
artifacts/migration/project_member_duplicate_relation_500_rollback_targets_v1.csv
```

Rollback must delete only:

```text
model = sc.project.member.staging
import_batch = ITER-2026-04-14-0030NZ
neutral_id in rollback target list
```
