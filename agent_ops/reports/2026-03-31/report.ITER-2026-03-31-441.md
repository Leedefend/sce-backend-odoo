# ITER-2026-03-31-441 Report

## Summary

- Reframed the bootstrap problem around actual operational need instead of the
  legacy hook shape.
- Separated repeat-safe platform baseline behavior from one-time fresh-DB
  initialization behavior.
- Froze the redesign so the next implementation batch can proceed with clear
  semantics.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-441.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-441.md`
- `agent_ops/state/task_results/ITER-2026-03-31-441.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-441.yaml` -> PASS
- repository audit of legacy hook + reset/verify/runbook references -> PASS

## Audit Result

The legacy bootstrap hook mixes two different semantics:

### A. Repeat-safe platform baseline

These operations are safe to treat as platform baseline behavior:

- activate target language
- set default `lang`
- set default `tz`
- set admin user `lang/tz`

These are idempotent and should remain safe even when the database already has
business data.

### B. One-time fresh-DB initialization

This operation is **not** repeat-safe:

- set company currency to the configured bootstrap currency

The failed `440` install proved that this is a one-time DB initialization step,
not a generic replayable platform bootstrap step.

## Outcome

Redesigned ownership:

1. `smart_platform_bootstrap`
   - owns only repeat-safe platform baseline behavior
   - must be safe to install on an already-used database

2. `smart_construction_bootstrap`
   - remains a temporary compatibility shim
   - temporarily owns the fresh-DB compatibility behavior that old reset flows
     still expect
   - specifically, the one-time company currency initialization can remain here
     while the shim still exists

3. downstream reset/verify/doc migration
   - may happen later
   - does not need to block the semantic redesign

This means the next implementation batch should:

- remove currency mutation from `smart_platform_bootstrap`
- keep only repeat-safe baseline logic there
- restore a narrow fresh-DB currency hook in the compatibility shim

## Risk Analysis

- Classification: `PASS`
- The redesign is coherent with the observed runtime failure and with the
  current reset-path dependency graph.
- No code changes were made in this batch.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-441.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-441.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-441.json`

## Next Suggestion

- Open the next implementation batch to apply the semantic split:
  - repeat-safe logic in `smart_platform_bootstrap`
  - fresh-DB currency compatibility in `smart_construction_bootstrap`
