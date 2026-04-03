# ITER-2026-04-03-889

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host primary-entry smoke landing strategy
- risk: medium
- publishability: not_publishable

## Summary of Change

- updated host smoke script:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- landing strategy now backend-semantic-first:
  - consume `project.entry.context.resolve` + `project.dashboard.enter`
  - build semantic entry URL candidates from backend route/scene key
  - add authenticated login fallback when landing on login surface
  - add native Odoo surface guard (`/web` / `.o_main_navbar`) to avoid accepting native frontend as success

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-889.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `semantic entry navigation failed after recovery attempts (27 tries)`
- `make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped after mandatory host gate failure in this batch

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260403T220746Z/summary.json`
- backend semantic facts still valid:
  - `backend_entry_route = /s/project.management`
  - `backend_scene_key = project.dashboard`
- navigation failures are all custom-frontend base candidates:
  - `http://127.0.0.1/?db=sc_demo&scene_key=project.dashboard`
  - `http://127.0.0.1/s/project.management?db=sc_demo`
  - `http://localhost/?db=sc_demo&scene_key=project.dashboard`
- no fallback acceptance to native Odoo surface in this batch

## Risk Analysis

- architecture boundary preserved:
  - frontend model-specific branching was not introduced
  - native frontend is now explicitly treated as invalid target for this gate
- current blocker moved to environment/runtime availability of custom frontend base entry
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-889.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-889.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-889.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated environment-availability batch:
  - freeze and verify the single custom-frontend entry base URL used by host gates
  - add a preflight reachability probe for custom frontend before expensive browser flow
  - rerun host smoke and then `verify.product.main_entry_convergence.v1`
