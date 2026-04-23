# Project member duplicate-relation write gate v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030NY`  
Database: `sc_demo`

## Purpose

Validate a 500-row duplicate-relation evidence slice before any neutral carrier
write.

This is a readonly gate. It does not write `sc.project.member.staging` and does
not write `project.responsibility`.

## Input

```text
artifacts/migration/project_member_neutral_expansion_duplicate_relation_evidence_slice_v1.csv
```

## Result

| Item | Count |
| --- | ---: |
| slice rows | 500 |
| distinct relation keys | 328 |
| max rows per relation key in slice | 5 |
| rollback plan rows | 500 |
| project.responsibility writes | 0 |
| db writes | 0 |

Blocking reasons:

```text
[]
```

## Boundary

The planned write is evidence-only. Multiple legacy rows can map to the same
`project_id/user_id` pair, so this batch must stay inside
`sc.project.member.staging`.

It must not be interpreted as:

- additional project responsibility roles;
- project visibility grants;
- approval or owner facts;
- workflow routing facts.

## Rollback Plan

```text
artifacts/migration/project_member_duplicate_relation_rollback_plan_v1.csv
```

If the next write task runs, rollback should target only records with:

```text
import_batch = ITER-2026-04-14-0030NY
legacy_member_id in rollback plan
```
