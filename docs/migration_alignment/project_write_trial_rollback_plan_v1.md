# Project Write Trial Rollback Plan v1

## Purpose

This plan defines how the 30-row project skeleton write trial could be rolled
back in a later explicitly authorized delete batch. This iteration does not
delete records.

## Rollback Scope

- Target database: `sc_demo`
- Target model: `project.project`
- Target count: 30
- Target selector: `legacy_project_id in locked 30-row set`
- Source lock list: `project_write_trial_rollback_target_v1.md`

## Preconditions

Rollback may start only if all conditions are true:

1. A new task contract explicitly authorizes database deletion.
2. The rollback script first runs in dry-run mode.
3. The dry-run target count is exactly 30.
4. Every target record has `legacy_project_id` in the locked list.
5. There are no duplicate `legacy_project_id` values.
6. The operator confirms no manual edits should be preserved.
7. No dependent records created by the trial need separate rollback.

If any condition fails, stop and require manual database review.

## Rollback Sequence

1. Read locked `legacy_project_id` list.
2. Query `project.project` for records matching the locked identities.
3. Refuse if the target count is not exactly 30.
4. Refuse if any matched record is outside the locked identity list.
5. Export a pre-delete target artifact with Odoo IDs, names, and identities.
6. Emit a dry-run deletion plan.
7. Require explicit delete-mode authorization in a separate batch.
8. Delete only the matched 30 records.
9. Commit only after all deletes succeed.
10. Export post-delete verification artifact.
11. Confirm the locked identities no longer exist.
12. Run static gate.

## Refusal Rules

The rollback must refuse to run if:

- target count is not 30;
- any locked identity is missing before rollback;
- any duplicate identity exists;
- a record is selected by project name or company text;
- any delete target lacks `legacy_project_id`;
- any delete target has an identity outside the lock list;
- rollback would delete company, partner, user, contract, payment, supplier,
  tax, bank, cost, settlement, or attachment records.

## Current Readiness

Rollback is executable as a later controlled batch because the target identities
are locked and unique. It is not authorized in this iteration.
