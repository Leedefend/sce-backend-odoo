# ITER-2026-03-31-411 Report

## Summary

- Froze the current user-bootstrap implementation boundary in the module README.
- Recorded that the current user model only supports one primary department.
- Explicitly prevented future batches from silently collapsing multi-department
  users into fake single-department truth.

## Changed Files

- `addons/smart_construction_custom/README.md`
- `agent_ops/tasks/ITER-2026-03-31-411.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-411.md`
- `agent_ops/state/task_results/ITER-2026-03-31-411.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-411.yaml` -> PASS

## Documentation Outcome

The README now explicitly states:

- current system support:
  - `res.users.sc_department_id`
  - primary department only
- current system gap:
  - no `extra_departments` field
  - no additional-department relation model in the active install chain

So later user bootstrap implementation must:

- allow:
  - user baseline write
  - company assignment
  - primary department assignment
- defer:
  - true multi-department persistence
  - additional-department storage

## Why This Batch Matters

Without this boundary, the next implementation batch could wrongly appear
"complete" while actually destroying accepted customer structure for the
confirmed multi-department users.

This batch keeps the customer truth frozen and separates:

- what is already supported by the active model
- what remains a later organization capability gap

## Risk Analysis

- Risk remained low.
- Documentation only.
- No addon implementation, user-write logic, security files, or manifests were
  changed.

## Rollback

- `git restore addons/smart_construction_custom/README.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-411.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-411.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-411.json`

## Next Suggestion

- Open the next implementation batch only for:
  - user baseline write
  - company assignment
  - primary department assignment
- Keep additional-department persistence in a separate future organization
  capability batch.
