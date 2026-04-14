# Project member no-placeholder safe slice v1

Status: L2 SAFE-SLICE READY  
Iteration: `ITER-2026-04-14-0030S`

The safe slice is intentionally smaller than the requested 50-100 row band
because the strict filter removes placeholder users and duplicate project/user
pairs.

## Safe Slice

- Path: `artifacts/migration/project_member_no_placeholder_safe_slice_v1.csv`
- Rows: 34
- Source: `artifacts/migration/project_member_source_shadow_v1.csv`

## Inclusion Rules

- project maps uniquely by `project.legacy_project_id`
- user maps to exactly one `res.users` record
- `user_match_mode` is not `placeholder_user`
- project/user pair appears once in the source
- no DB write was performed

## Write Boundary

The next L3 write task may use only this 34-row safe slice unless a new screen
task expands the candidate set. It must still create rollback targets and run a
post-write readonly review.
