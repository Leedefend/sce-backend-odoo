# Project member responsibility promotion candidate screen v1

Status: PASS  
Iteration: `ITER-2026-04-14-0030ZC`

## Purpose

Screen consolidated project/user pairs for responsibility promotion readiness.

This batch is readonly. It does not write `project.responsibility` and does not
change record rules, ACLs, role keys, or neutral evidence rows.

## Gate

A pair can be a promotion candidate only when:

- `project_id` is present;
- `user_id` is present;
- verified role fact exists;
- target `role_key` can be derived from that verified role fact;
- existing `project.responsibility` conflicts are reviewed.

## Expected Current Result

All current consolidated pairs have:

```text
role_fact_status = missing
```

Therefore current promotion candidates are expected to be:

```text
0
```

## Result

| Item | Count |
| --- | ---: |
| total pairs | 362 |
| promotion candidate pairs | 0 |
| blocked pairs | 362 |
| missing role fact pairs | 362 |
| missing target role key pairs | 362 |
| existing responsibility pair review pairs | 0 |

Current conclusion:

```text
No consolidated pair is eligible for project.responsibility promotion yet.
```

## Outputs

```text
artifacts/migration/project_member_responsibility_promotion_candidates_v1.json
artifacts/migration/project_member_responsibility_promotion_candidates_v1.csv
artifacts/migration/project_member_responsibility_promotion_screen_summary_v1.json
```
