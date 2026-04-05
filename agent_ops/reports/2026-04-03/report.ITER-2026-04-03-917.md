# ITER-2026-04-03-917

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: smoke observability reporter
- risk: low
- publishability: publishable

## Summary of Change

- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- implementation:
  - added `summary.http_5xx_resources` field.
  - added `page.on('response')` capture for `status >= 500`.
  - recorded `{status,url,method,resource_type}` with de-duplication.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-917.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS

## Key Evidence

- smoke summary:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T071637Z/summary.json`
- captured 5xx resource:
  - `POST http://127.0.0.1/api/v1/intent?db=sc_demo` (status 500, type `fetch`)

## Risk Analysis

- low risk: additive observability only, no entry semantic behavior change.
- actionable finding:
  - 500 noise now deterministically tied to `127.0.0.1` intent endpoint call, enabling focused next fix.

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-917.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-917.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-917.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open low-risk implement batch to normalize frontend runtime intent base/origin selection and prevent `127.0.0.1` fallback fetch path from emitting 500.
