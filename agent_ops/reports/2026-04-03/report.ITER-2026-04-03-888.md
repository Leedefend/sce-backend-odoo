# ITER-2026-04-03-888

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: PM role surface entry semantic policy
- risk: medium
- publishability: not_publishable

## Summary of Change

- backend-only semantic convergence in:
  - `addons/smart_construction_scene/core_extension.py`
- PM role surface policy updated:
  - landing candidates switched to project-management first:
    - `project.management`
    - `project.dashboard`
    - `projects.intake`
    - `projects.list`
    - `projects.ledger`
    - `my_work.workspace`
  - explicit allowlist added for:
    - `smart_construction_core.menu_sc_project_management_scene`
    - `smart_construction_core.menu_sc_project_dashboard`
  - removed PM menu blocklist on `menu_sc_project_manage`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-888.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `page.waitForFunction: Timeout 30000ms exceeded`
- `make verify.product.main_entry_convergence.v1`: FAIL
  - upstream contract/management checks PASS
  - failed at `verify.portal.project_dashboard_primary_entry_browser_smoke.host`

## Key Evidence

- backend semantic probe (login + `system.init`) confirms PM landing semantics fixed:
  - `default_route.scene_key = project.management`
  - `default_route.route = /s/project.management`
  - `role_surface.landing_scene_key = project.management`
  - `role_surface.menu_blocklist_xmlids = []`
- latest host smoke artifact still fails at dashboard readiness wait:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260403T192943Z/summary.json`
  - status `FAIL`, error `Timeout 30000ms exceeded`
  - console includes frontend localization fetch failure in lazy frontend assets

## Risk Analysis

- architecture boundary is preserved: no frontend model-specific branching added
- backend entry semantics are now aligned, but real-user host flow remains blocked
- release publishability remains `not_publishable`

## Rollback Suggestion

- `git restore addons/smart_construction_scene/core_extension.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-888.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-888.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-888.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open a dedicated low-risk host-smoke chain batch:
  - keep backend semantic entry as source of truth
  - align smoke landing/wait strategy with custom-frontend authenticated shell readiness
  - remove remaining false-negative path caused by frontend lazy localization bootstrap race
