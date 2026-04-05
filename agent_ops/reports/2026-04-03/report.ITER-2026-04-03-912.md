# ITER-2026-04-03-912

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: project dashboard semantic supplier
- risk: low
- publishability: publishable

## Summary of Change

- updated:
  - `addons/smart_construction_core/services/project_dashboard_service.py`
- implementation:
  - added `_NullEvidenceSummaryService` fallback provider.
  - replaced hard lookup `env["sc.evidence.summary.service"]` with safe resolver `_model(...)` and fallback.
  - ensured `project.entry.context.resolve` degrades to valid semantic response instead of 500 when evidence summary service is absent.
- runtime apply:
  - restarted `sc-backend-odoo-prod-sim-odoo-1` to load backend patch.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-912.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.product.main_entry_convergence.v1`: PASS
- direct intent probe:
  - `login`: 200
  - `project.entry.context.resolve`: 200
  - returns fallback route `/my-work` with empty project context when no project is resolved.

## Key Evidence

- smoke artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T063934Z/summary.json`
- evidence in artifact:
  - `backend_entry_route` present (`/my-work`)
  - no `backend_entry_route_error`
  - `console_errors` empty

## Risk Analysis

- low code risk:
  - additive fallback only, no contract field removals.
- residual product risk:
  - fallback route `/my-work` indicates no project context available in `sc_demo`; semantic behavior is stable but depends on data availability.

## Rollback Suggestion

- `git restore addons/smart_construction_core/services/project_dashboard_service.py`
- `git restore agent_ops/tasks/ITER-2026-04-03-912.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-912.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-912.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open next low-risk backend semantic-supply batch to materialize demo project context in `sc_demo` (if product expectation requires `/s/project.management` instead of `/my-work`).
