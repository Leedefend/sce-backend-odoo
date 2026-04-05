# ITER-2026-04-03-906

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host connectivity diagnostics continuation policy
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-906.yaml`
- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- diagnostics degradation enhancement:
  - when TCP probe fails with `EPERM`, diagnostics now marks degraded mode instead of hard-stop
  - `connectivity_diagnostics` now emits:
    - `last_error: tcp_permission_blocked`
    - `degraded: true`
  - host flow continues to login preflight under degraded diagnostics

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-906.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost:8069 make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - runtime probe reused cache PASS
  - preflight reached and failed with endpoint connect permission error:
    - `custom_frontend_entry_unreachable: apiRequestContext.get: connect EPERM 127.0.0.1:8069`
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost:8069 make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped due stop rule after first `make verify.*` failure

## Key Evidence

- host smoke artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T031400Z/summary.json`
- progression signal:
  - diagnostics no longer terminate early on TCP `EPERM`
  - failure now deterministically lands at login preflight transport layer with explicit EPERM connect evidence

## Risk Analysis

- code risk remains low:
  - scope limited to diagnostics continuation policy
- runtime risk remains high:
  - gateway connection is blocked by host permission constraints (`connect EPERM`)
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-906.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-906.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-906.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated host permission-lane recovery batch:
  - classify and mitigate loopback connect `EPERM` for gateway port
  - rerun explicit-gateway host gate once permission lane is recovered
