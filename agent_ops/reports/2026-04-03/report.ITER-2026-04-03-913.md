# ITER-2026-04-03-913

- status: PASS
- mode: screen
- layer_target: Product Release Usability Proof
- module: project entry semantic supply
- risk: low
- publishability: publishable

## Summary of Screen Result

- classified fallback reason:
  - `data_absence_in_business_fact_layer`
- evidence:
  - smoke artifact route: `/my-work`
  - smoke artifact project context: `project_id=0`
  - database fact: `sc_demo.project_project` count is `0`
- conclusion:
  - fallback is expected behavior under current backend semantics because no project business fact exists in sc_demo.
  - this is not a frontend consumer issue and not a scene-orchestration exception now.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-913.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS

## Key Evidence

- smoke summary:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260404T064439Z/summary.json`
- db check:
  - `select count(*) from project_project;` => `0`
  - no rows in `project_project`

## Risk Analysis

- low risk in this batch (screen-only, no code changes)
- implementation direction risk:
  - if product requires `/s/project.management` on fresh runtime, must supply project business facts (seed/bootstrap path), not frontend special-case.

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-04-03-913.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-913.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-913.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open implement batch at `business-fact layer` to provide minimal reproducible project seed in `sc_demo` (or equivalent bootstrap path), then re-verify entry route convergence.
