# Project member neutral to responsibility promotion gate v1

Status: FROZEN_BLOCKED_WITHOUT_ROLE_FACT  
Iteration: `ITER-2026-04-14-0030ZA`

## Gate

A consolidated pair may be considered for promotion to `project.responsibility`
only when all conditions are true:

- `project_id` is confirmed;
- `user_id` is confirmed;
- a verifiable role fact exists;
- target `role_key` is valid;
- no existing `project.responsibility` conflict exists for the promoted
  project/user/role;
- record-rule and visibility impact are explicitly reviewed in a dedicated
  authority-path task;
- rollback target is generated.

## Missing Role Fact

If the role fact is missing, promotion is blocked.

Current neutral rows have `role_fact_status = missing`, so no row or pair is
eligible for responsibility promotion in this batch.

## Manual Approval

Manual approval may allow a default role only if a future task records:

- the approved default role;
- the business reason;
- the risk acceptor;
- the expected visibility and responsibility impact;
- rollback scope.

Absent that approval, no default `role_key` is allowed.

## Promotion Unit

Promotion should be evaluated at the consolidated pair level, not by raw
evidence row count.

The resulting responsibility record must still link back to the underlying
evidence rows for auditability.

## This Batch

This batch does not promote any row or pair.
