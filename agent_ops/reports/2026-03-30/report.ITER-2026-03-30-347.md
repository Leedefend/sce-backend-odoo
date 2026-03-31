# ITER-2026-03-30-347 Report

## Summary

- Switched the investigation line from platform/frontend phenomena to business-fact audit for the 21 published preview menus.
- Added a repeatable fact-audit script that joins runtime preview menu metadata with source menus, actions, views, and ACL files.
- Verified that the demo PM user has no obvious menu-group or ACL mismatch across the current 21 preview menus.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-347.yaml`
- `scripts/verify/preview_menu_fact_audit.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-347.yaml` -> PASS
- `python3 scripts/verify/preview_menu_fact_audit.py` -> PASS

## Fact Findings

- `16` preview menus are backed by native `ir.actions.act_window`.
- `3` preview menus are backed by native `ir.actions.act_url`:
  - `工作台`
  - `生命周期驾驶舱`
  - `能力矩阵`
- `1` preview menu is backed by a native `ir.actions.server`:
  - `执行结构`
- `1` preview menu is a pure `scene_route_only` entry with no native action:
  - `smart_construction_core.menu_sc_project_management_scene`
- For demo PM, the audit found no direct menu-group mismatch and no direct ACL mismatch in the current preview set.

## Risk Analysis

- Risk level remains low for this audit batch because it is evidence-only.
- The next real product risk is no longer generic permission denial; it is semantic/data-path correctness for non-`act_window` entries.
- The highest-priority business-fact cluster is:
  - `act_url` menus
  - `ir.actions.server` menus
  - `scene_route_only` menus

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-347.yaml`
- `git restore scripts/verify/preview_menu_fact_audit.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-347.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-347.json`

## Next Suggestion

- Start the next fact-layer batch on the non-`act_window` set first, focusing on:
  - `smart_construction_core.menu_sc_project_management_scene`
  - `smart_construction_core.action_exec_structure_entry`
  - `smart_construction_portal.action_sc_portal_dashboard`
  - `smart_construction_portal.action_sc_portal_lifecycle`
  - `smart_construction_portal.action_sc_portal_capability_matrix`
- For that batch, trace each item’s minimum data prerequisite and actual business meaning so the published menu label matches the underlying industry function.
