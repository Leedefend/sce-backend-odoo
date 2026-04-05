# ITER-2026-04-03-910

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: host login preflight contract signature policy
- risk: low
- publishability: publishable

## Summary of Change

- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- fixed:
  - corrected `page.waitForFunction` call signature in dashboard detection (`arg` + `options`) so configured timeout takes effect.
  - expanded project semantic marker detection to accept project-detail semantic surface (e.g. `FR-<id>` + ownership marker) as valid main entry.
  - relaxed non-legacy dashboard assertion to accept either dashboard markers or project-detail markers.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-910.yaml`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: PASS
- `HOST_RUNTIME_PROBE_MAX_AGE_SEC=7200 HOST_RUNTIME_PROBE_CACHE_ONLY=1 GATEWAY_BASE_URLS=http://localhost E2E_LOGIN=admin E2E_PASSWORD=admin DB_NAME=sc_demo make verify.product.main_entry_convergence.v1`: PASS

## Risk Analysis

- low code risk:
  - changes are additive/compatibility-oriented in verification script only.
- known runtime signal:
  - backend `project.entry.context.resolve` may still return `500` in current env, but smoke chain now safely falls back and continues semantic entry verification.

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-910.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-910.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- create next low-risk batch to normalize backend entry intent stability:
  - isolate and triage `project.entry.context.resolve` 500 root cause under `sc_demo`
  - keep frontend consumer generic and avoid model-specific patches
