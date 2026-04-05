# ITER-2026-04-03-892

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host login route contract binding
- risk: low
- publishability: not_publishable

## Summary of Change

- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- preflight route binding improved:
  - validate custom login contract on route set:
    - `/web/login?db=...`
    - `/login?db=...`
  - accept first valid custom login surface and persist:
    - `effective_base_url`
    - `effective_login_url`
  - narrowed 404 detection to real 404 phrase only, reducing false negatives

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-892.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `native_odoo_surface_detected`
- `make verify.product.main_entry_convergence.v1`: FAIL
  - upstream contract/management chain PASS
  - host gate fails with same `native_odoo_surface_detected`

## Key Evidence

- latest artifact:
  - `artifacts/codex/project-dashboard-primary-entry-browser-smoke/20260403T224742Z/summary.json`
- preflight now succeeds:
  - `preflight_ok = true`
  - `effective_login_url = http://localhost:8070/web/login?db=sc_demo`
  - first check status `200`, `has_login_signature = true`
- remaining blocker:
  - after semantic entry navigation, page resolves to native Odoo surface and is rejected by guard

## Risk Analysis

- signal quality improved:
  - login route contract no longer blocks this batch
  - true blocker now isolated to entry routing into native surface
- architecture boundary preserved:
  - native frontend still prohibited as success target
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-892.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-892.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-892.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated routing-governance batch:
  - bind semantic entry `/s/project.management` and `scene_key=project.dashboard` to custom frontend scene shell
  - prevent fallback to native Odoo shell on this chain
  - rerun host gate and full convergence gate
