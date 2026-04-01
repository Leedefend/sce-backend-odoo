# ITER-2026-03-31-439 Report

## Summary

- Added a narrow AGENTS exception for the dedicated
  `smart_construction_bootstrap -> smart_platform_bootstrap` migration line.
- Kept the default `__manifest__.py` stop rule intact for ordinary batches.
- Limited the exception to the exact bootstrap migration scope and frozen
  transition order.

## Changed Files

- `AGENTS.md`
- `agent_ops/tasks/ITER-2026-03-31-439.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-439.md`
- `agent_ops/state/task_results/ITER-2026-03-31-439.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-439.yaml` -> PASS
- `AGENTS.md` manual audit for narrow scope and preserved default stop rule -> PASS

## Audit Result

The new rule does **not** generally allow manifest edits.

It only allows controlled manifest changes when all of the following are true:

- the task is a dedicated bootstrap-module migration batch
- the user explicitly authorizes that high-risk batch
- the allowlist names the exact manifest and related bootstrap reference files
- the implementation is limited to:
  - creating `smart_platform_bootstrap`
  - keeping `smart_construction_bootstrap` as a compatibility shim
  - migrating references in the frozen order from `438`

This keeps the original repository stop policy intact while allowing the next
high-risk migration batch to proceed legally.

## Outcome

The execution guard is now ready for the actual bootstrap migration
implementation line.

## Risk Analysis

- Classification: `PASS`
- This was a governance-only guard update.
- Risk remains contained because the exception is narrower than the generic stop
  rule and does not authorize unrelated manifest churn.

## Rollback

- `git restore AGENTS.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-439.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-439.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-439.json`

## Next Suggestion

- Open the first high-risk implementation batch for:
  - creating `smart_platform_bootstrap`
  - wiring the compatibility shim in `smart_construction_bootstrap`
