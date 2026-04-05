# ITER-2026-04-03-897

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host diagnostics origin discovery
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-897.yaml`
- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- origin fallback discovery enhancement:
  - added env-driven origin fallbacks via `BASE_URL_FALLBACKS`
  - added bounded localhost/loopback fallbacks for common ports (`80`, `8069`) when base is `:8070`
  - diagnostics now probes broader local origin set before preflight decision

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-897.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `custom_frontend_entry_unreachable: socket hang up`
- `make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped due stop rule after first `make verify.*` failure

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T014217Z/summary.json`
- diagnostics signal after fallback discovery:
  - `localhost/127.0.0.1:8069` now TCP reachable
  - login route HTTP stage on `:8069` fails with `socket hang up`
  - preflight remains unreachable for custom-login contract

## Risk Analysis

- code risk remains low:
  - change is limited to origin candidate discovery and diagnostics coverage
- runtime risk remains high:
  - reachability improved from pure timeout to `socket hang up`, indicating upstream service handshake instability
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-897.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-897.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-897.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated host-login handshake recovery batch:
  - classify reverse-proxy/app handshake path for `/web/login` and `/login` on reachable origin
  - bind host smoke BASE_URL to verified custom-login endpoint once handshake is stable
