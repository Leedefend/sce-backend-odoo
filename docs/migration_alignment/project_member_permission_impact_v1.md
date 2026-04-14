# Project member permission impact v1

Status: WRITE-BLOCKED  
Iteration: `ITER-2026-04-14-0030R`

project_member facts are permission-sensitive. They must not be written until
authority impact is explicitly screened and approved.

## Impact Areas

| Area | Impact |
| --- | --- |
| record rules | Yes. project_member facts are candidate access truth and can alter project visibility. |
| project visibility | Yes. member bindings may grant or deny project/task visibility. |
| responsibility logic | Yes. member bindings may affect owner/PM/member responsibility workflows. |

## Current Dry-Run Findings

- Total rows: 21390
- Project mapping: 21390 mapped, 0 unmapped
- User mapping: 7389 mapped, 14001 placeholder classifications
- Duplicate project/user pairs: 3

## Write Blockers

- `placeholder_user` appears in 14001 rows.
- There is no approved fallback-user policy.
- There is no approved rule-impact safe slice.
- There is no rollback model for member visibility side effects.

## Required Before Write

- A no-placeholder safe slice.
- Explicit authority decision for unmapped users.
- Record-rule and visibility impact review.
- Rollback target format keyed by legacy member id and project/user mapping.
- Dedicated L3 write task with no ACL or record-rule file changes.
