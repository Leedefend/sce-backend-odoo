# ITER-2026-03-31-413 Report

## Summary

- Executed the customer bootstrap in `sc_demo` through a controlled Odoo shell path.
- Confirmed that the customer company, six departments, and the frozen 20-user baseline were actually persisted.
- Confirmed that accepted multi-department truth is currently preserved only as deferred runtime output, not as extra-department persistence.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-413.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-413.md`
- `agent_ops/state/task_results/ITER-2026-03-31-413.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-413.yaml` -> PASS
- runtime execution in `sc_demo` via direct Odoo container shell -> PASS

## Runtime Audit Result

Persisted state observed in `sc_demo`:

- company:
  - `四川保盛建设集团有限公司`
- departments:
  - `工程部`
  - `成控部`
  - `经营部`
  - `行政部`
  - `财务部`
  - `项目部`
- department count:
  - `6`
- user count under the frozen customer login set:
  - `20`

Bootstrap write result:

- created users:
  - `19`
- updated users:
  - `1`
    - `admin`
- unresolved departments:
  - none

Primary-department landing result:

- `duanyijun` -> `经营部`
- `chentianyou` -> `工程部`
- `jiangyijiao` -> `经营部`
- `chenshuai` -> `成控部`
- `wutao` -> `项目部`
- `lidexue` -> `项目部`
- `hujun` -> `项目部`

Role-only / no-department users persisted as expected:

- `admin` -> no primary department
- `shuiwujingbanren` -> no primary department

Deferred extra departments remained in runtime output only:

- `duanyijun` -> `行政部`
- `chentianyou` -> `行政部`
- `jiangyijiao` -> `行政部`, `财务部`, `项目部`
- `chenshuai` -> `项目部`

## Implementation Outcome

The customer bootstrap chain is now no longer just implemented in code. It has
been executed and observed in the active demo database.

This means the current customer bootstrap slice now has a real closed loop for:

- company root creation/update
- six root department creation/update
- frozen customer user creation/update
- primary department persistence

The current boundary remains unchanged:

- additional departments are not persisted yet
- post persistence is still deferred
- system-role persistence is still deferred

## Risk Analysis

- Risk remained low.
- No addon code changed in this batch.
- Runtime execution was successful and the result was clear.

Non-blocking runtime note:

- The company create/update path triggered a partner enrichment log line during execution.
- This did not block bootstrap persistence or leave unresolved runtime state.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-413.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-413.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-413.json`

## Next Suggestion

- Open the next additive implementation batch for post attachment and system-role attachment.
- Keep multi-department persistence as a separate organization-capability batch rather than mixing it into role/bootstrap work.
