# ITER-2026-03-30-367 Report

## Summary

- Polished the native `工程结构` landing page for demo PM users.
- Added a default `按项目` grouping so the first screen no longer opens as an undifferentiated flat list.
- Added a small help block to explain the intended project-oriented usage.

## Changed Files

- `addons/smart_construction_core/views/support/work_breakdown_views.xml`
- `agent_ops/tasks/ITER-2026-03-30-367.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-367.md`
- `agent_ops/state/task_results/ITER-2026-03-30-367.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-367.yaml` -> PASS
- `make verify.smart_core` -> PASS

## Behavior Change

- `action_work_breakdown` now preloads:
  - `search_default_group_project = 1`
- `action_work_breakdown` now includes a help block that tells the user:
  - the page is meant to be read from the project dimension first
  - further narrowing can continue by level or parent node

## User Outcome

- Demo PM users entering `工程结构` now see a grouped landing that matches how the seeded WBS facts are organized.
- The page explains itself better without adding more demo data or custom frontend work.
- This closes the residual native PM polish tail identified by `366`.

## Risk Analysis

- Risk remains low.
- The batch is limited to one native `act_window` action definition.
- No models, ACL, manifests, demo data, or frontend code were changed.

## Rollback

- `git restore addons/smart_construction_core/views/support/work_breakdown_views.xml`
- `git restore agent_ops/tasks/ITER-2026-03-30-367.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-367.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-367.json`

## Next Suggestion

- Close the native PM trio line as complete.
- Open the next read-only audit on the finance-generated native pages `资金台账 / 付款记录`, focusing on demo PM first-screen value rather than raw reachability.
