# ITER-2026-04-03-907

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host preflight permission-lane fast classifier
- risk: low
- publishability: not_publishable

## Summary of Change

- created:
  - `agent_ops/tasks/ITER-2026-04-03-907.yaml`
- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- EPERM fast-path enhancement:
  - added `connect EPERM` fast classifier in preflight transport chain
  - on EPERM detection, preflight emits `eperm_fast_path` marker
  - origin handshake counter is force-elevated to trigger immediate origin short-circuit

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-907.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost:8069 make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `custom_frontend_entry_unreachable: connect EPERM 127.0.0.1:8069`
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost:8069 make verify.product.main_entry_convergence.v1`: NOT_RUN
  - skipped due stop rule after first `make verify.*` failure

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T031912Z/summary.json`
- evidence markers now present:
  - `transport = eperm_fast_path`
  - `transport = origin_short_circuit`
  - retries are significantly reduced under EPERM lane

## Risk Analysis

- code risk remains low:
  - change confined to failure classification and retry suppression in verification script
- runtime risk remains high:
  - host permission lane still blocks explicit gateway connect (`EPERM`)
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-907.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-907.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-907.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated permission-lane bypass strategy batch:
  - introduce explicit `permission_lane_blocked` top-level classifier
  - fail fast before login intent path when gateway connect EPERM is deterministic
