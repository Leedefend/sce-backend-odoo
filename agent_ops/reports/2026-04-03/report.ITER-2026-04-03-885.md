# ITER-2026-04-03-885

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host runtime pre-gate
- risk: medium
- publishability: not_publishable

## Summary of Change

- added deterministic host runtime probe:
  - `scripts/verify/host_browser_runtime_probe.mjs`
- integrated probe before host primary-entry smoke:
  - `Makefile` target `verify.portal.host_browser_runtime_probe`
  - `verify.portal.project_dashboard_primary_entry_browser_smoke.host` now invokes probe first
- expanded host runtime bootstrap dependencies:
  - `scripts/verify/bootstrap_playwright_host_runtime.sh` now includes
    `libdatrie.so.1` / `libgraphite2.so.3` and corresponding packages
- hardened browser launch policy in host probe + primary-entry smoke:
  - default headless-shell launch now retries up to 3 attempts
  - full-chrome fallback now only triggers for missing-shared-library failures

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-885.yaml`: PASS
- `make verify.portal.host_browser_runtime_probe`: PASS (latest run: `20260403T134657Z`)
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - pre-gate stable PASS
  - host smoke now reaches login and post-login routing, but target dashboard contract still fails:
    - `/s/project.management` on host returns 404 in current runtime
    - dashboard readiness selectors (`state-explain-card`) not satisfied on resolved page
- `make verify.product.main_entry_convergence.v1`: FAIL
  - management acceptance chain still PASS
  - host entry stage remains failure point

## Risk Analysis

- blocker is now narrowed from launch-level instability to host entry contract mismatch
  after login (target route/readiness semantics drift)
- release-grade host evidence remains unavailable; publishability cannot be approved

## Rollback Suggestion

- `git restore scripts/verify/host_browser_runtime_probe.mjs`
- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-03-885.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-885.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-885.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- move to dedicated host entry contract alignment batch:
  - freeze canonical post-login entry route for project-management dashboard on host
  - align smoke assertions to canonical semantic markers (not stale CSS-only selectors)
  - rerun release-grade host gates:
  - `verify.portal.host_browser_runtime_probe`
  - `verify.portal.project_dashboard_primary_entry_browser_smoke.host`
  - `verify.product.main_entry_convergence.v1`
