# ITER-2026-04-03-893

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host semantic entry route ordering governance
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-893.yaml`
- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- route-order governance:
  - semantic entry candidates now prioritize backend `route` URL before root-level scene-key fallback
  - root fallback remains available as a degraded candidate instead of first-hop navigation target

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-893.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `custom_frontend_entry_unreachable: This operation was aborted`
- `make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped due stop rule after first `make verify.*` failure

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T011842Z/summary.json`
- failure profile:
  - custom-frontend preflight all login candidates aborted (~6s each)
  - no semantic-entry routing assertion reached in this run

## Risk Analysis

- code risk remains low:
  - change is bounded to URL candidate ordering in host verification script
- runtime risk remains medium:
  - host runtime preflight currently unstable (`fetch` abort) and blocks semantic gate execution
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-893.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-893.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-893.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open a dedicated host-runtime reachability stabilization batch:
  - classify and harden `fetch` abort handling in login preflight probes
  - re-run host gate first, then convergence gate only when host gate passes
