# ITER-2026-04-03-886

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: sidebar runtime robustness + backend semantic entry consumption
- risk: medium
- publishability: not_publishable

## Summary of Change

- hardened sidebar runtime shape guards in:
  - `addons/smart_construction_core/static/src/js/sc_sidebar.js`
  - protected `findFirstActionFromSections` / `findSectionById` against non-array `domain.sections`
  - normalized `domainSections` at load time to avoid iterable crashes
- upgraded host primary-entry smoke semantics in:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
  - consume backend intent semantics:
    - `project.entry.context.resolve`
    - `project.dashboard.enter` (`scene_key`)
  - route handling switched to backend-driven scene-key entry URL
  - dual-profile dashboard detection and UI navigation fallback remained enabled

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-886.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - runtime probe: PASS
  - host custom-frontend still lands/stays on collaboration shell page
  - dashboard semantic detection times out
- `make verify.product.main_entry_convergence.v1`: FAIL
  - management acceptance chain: PASS
  - host primary-entry stage: FAIL at dashboard detection timeout

## Key Evidence

- previous blocking runtime error `domain.sections is not iterable` is no longer present after restart
- backend semantic facts are available and stable:
  - `project.entry.context.resolve`: `route=/s/project.management`
  - `project.dashboard.enter`: `scene_key=project.dashboard`
- despite backend semantic availability, current host custom-frontend main entry does not consume and route to dashboard scene in this flow

## Risk Analysis

- release gate remains blocked at host real-user entry
- blocker has been narrowed to semantic-consumption/linkage gap between backend-provided primary-entry semantics and current frontend entry state machine
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore addons/smart_construction_core/static/src/js/sc_sidebar.js`
- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-886.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-886.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-886.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated backend-orchestration batch:
  - freeze single canonical primary-entry semantic (`scene_key` + route contract alignment)
  - align `project.entry.context.resolve` and `project.dashboard.enter` to one consumable entry contract
  - ensure host custom-frontend root entry consumes that contract without relying on hard route jumps
- then rerun:
  - `verify.portal.project_dashboard_primary_entry_browser_smoke.host`
  - `verify.product.main_entry_convergence.v1`
