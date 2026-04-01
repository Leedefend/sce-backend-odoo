# ITER-2026-03-31-418 Report

## Summary

- Narrowly amended the repository execution rule in `AGENTS.md`.
- The generic stop condition for `security/**` remains the default.
- A dedicated exception now exists for explicitly authorized, task-bounded,
  high-risk permission-governance batches.

## Changed Files

- `AGENTS.md`
- `agent_ops/tasks/ITER-2026-03-31-418.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-418.md`
- `agent_ops/state/task_results/ITER-2026-03-31-418.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-418.yaml` -> PASS

## Rule Amendment

Updated:

- `AGENTS.md`

New rule semantics:

- ordinary batches still stop immediately on `security/**`
- `security/**` implementation is only allowed when:
  - there is a dedicated high-risk permission-governance task
  - the task allowlist explicitly includes the touched `security/**` paths
  - the user has explicitly authorized that batch
  - the change stays additive and authority-path-scoped
- `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`, and financial
  domains remain excluded unless separately authorized by a new task line

## Risk Analysis

- Risk remained low in this batch because no addon implementation or security
  payload changed.
- The amendment is narrow and does not convert `security/**` into a generally
  open path.

## Rollback

- `git restore AGENTS.md`
- `git restore agent_ops/tasks/ITER-2026-03-31-418.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-418.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-418.json`

## Next Suggestion

- Resume `ITER-2026-03-31-417` under the new narrow exception and implement the
  dedicated business-system-admin authority path.
