# ITER-2026-03-30-348 Report

## Summary

- Completed the focused audit of the five non-`act_window` preview menus.
- Split these menus into two responsibility layers:
  - native business-fact entries that remain valid in the original model/menu/action system
  - portal-style entries that should be fulfilled by the custom frontend instead of the abandoned native portal frontend
- Re-anchored the next product line from generic “semantic alignment” to an explicit publication policy: original business facts stay native, portal rendering moves to the custom frontend supplement layer.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-30-348.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-348.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-348.yaml` -> PASS

## Fact Findings

- `smart_construction_core.menu_sc_project_management_scene`
  - native fact type: `scene_route_only`
  - business target: `/s/project.management`
  - prerequisite: at least one resolvable project context; otherwise `ProjectEntryContextService` falls back to `/my-work`
  - diagnosis: this is still a valid native business-fact entry, but it is context-sensitive rather than portal-driven

- `smart_construction_core.action_exec_structure_entry`
  - native fact type: `ir.actions.server`
  - business target: execution-structure flow anchored on a selected project
  - prerequisite: project context must exist; otherwise the server action intentionally warns and redirects the user to the project list
  - diagnosis: this is a valid native business-fact entry and should remain in the native availability line

- `smart_construction_portal.action_sc_portal_dashboard`
- `smart_construction_portal.action_sc_portal_lifecycle`
- `smart_construction_portal.action_sc_portal_capability_matrix`
  - native fact type: `ir.actions.act_url`
  - original route targets: `/portal/dashboard`, `/portal/lifecycle`, `/portal/capability-matrix`
  - extra runtime prerequisites:
    - portal session or token bridge
    - portal-specific controller flow
    - feature flags under `sc.portal.*.enabled`
  - diagnosis: these actions are still valid as native publication anchors, but their usable rendering surface should now be provided by the custom frontend instead of the original portal frontend

## Risk Analysis

- Risk level remains low because this batch is audit-only.
- The main governance risk was semantic confusion: portal actions were being interpreted as native-front-end usability obligations.
- That ambiguity is now resolved:
  - native fact layer owns `model / menu / action`
  - custom frontend owns the user-facing rendering and interaction layer for portal-style entries

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-30-348.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-348.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-348.json`

## Next Suggestion

- Start the next governance batch by formalizing preview publication policy into two lanes:
  - native business-fact lane: menus/actions that remain directly grounded in original business facts
  - custom-frontend supplement lane: portal-style or special rendering entries that are published from native facts but fulfilled by the custom frontend
