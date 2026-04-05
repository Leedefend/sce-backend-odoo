# ITER-2026-04-03-899

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host login preflight endpoint strategy
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-899.yaml`
- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- endpoint strategy enhancement:
  - preflight origin ordering now uses diagnostics-derived scores (TCP/HTTP signal)
  - added origin-family handshake-failure counter and `origin_short_circuit` guard
  - repeated handshake-failing origins are cut early to reduce timeout cost

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-899.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `custom_frontend_entry_unreachable: apiRequestContext.get: Timeout 12000ms exceeded`
- `make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped due stop rule after first `make verify.*` failure

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T020920Z/summary.json`
- evidence progression:
  - diagnostics-ranked origins now start with TCP-ready `:8069` family
  - `origin_short_circuit` markers appear for repeated handshake failures
  - final blocker remains login handshake failure/timeouts across all candidate origins

## Risk Analysis

- code risk remains low:
  - logic is bounded to verification endpoint ordering and retry short-circuit
- runtime risk remains high:
  - no origin returns valid login contract signature; transport failures persist
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-899.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-899.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-899.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated endpoint-binding governance batch:
  - bind host smoke to confirmed custom-frontend gateway origin via explicit env contract
  - isolate/remove non-gateway fallback origins from production verification lane
