# ITER-2026-03-30-363 Report

## Summary

- Repaired the narrowest remaining native-fact usability gap identified by the fact-chain audit: the `执行结构` preview menu.
- Upgraded the menu entry from a generic warn-and-list fallback to a first-success bridge:
  - when exactly one reachable project exists, the menu opens that project's WBS directly
  - when multiple project choices exist, the menu still warns, but now redirects to the lifecycle project list with `我的项目` prefiltered
- Kept the repair fully inside the original menu/action chain without reintroducing scene semantics into the industry fact layer.

## Changed Files

- `addons/smart_construction_core/actions/execution_structure_actions_base.xml`
- `agent_ops/tasks/ITER-2026-03-30-363.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-363.md`
- `agent_ops/state/task_results/ITER-2026-03-30-363.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-363.yaml` -> PASS
- `make verify.smart_core` -> PASS

## Behavior Change

Before:

- the menu always showed a warning
- the fallback always jumped to a generic project list
- users still had to recover the right project path manually

After:

- if PM only has one reachable project in the standard "我的项目" domain, the entry opens `smart_construction_core.action_exec_structure_wbs` directly with that project injected into context and domain
- otherwise, the warning remains, but the fallback now jumps to `smart_construction_core.action_sc_project_kanban_lifecycle`
- the fallback preloads `search_default_filter_my_projects=1`, so the user lands in a narrower project-selection surface instead of a broad generic list

## Risk Analysis

- Risk level remains medium-to-low because the change only touches one server action entry bridge.
- No ACL, security, manifest, payment, settlement, account, or frontend code was changed.
- The repair is additive and reversible:
  - native WBS entry behavior remains unchanged for project-scoped openings
  - only the no-context menu entry branch is improved

## Rollback

- `git restore addons/smart_construction_core/actions/execution_structure_actions_base.xml`
- `git restore agent_ops/tasks/ITER-2026-03-30-363.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-363.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-363.json`

## Next Suggestion

- The native-fact repair line can now shift from entry bridging to data-quality/value checks on the remaining `act_window` pages.
- The separate custom-frontend lane remains unchanged:
  - `工作台`
  - `生命周期驾驶舱`
  - `能力矩阵`
  - `项目驾驶舱(scene)`
