# ITER-2026-04-03-890

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host smoke preflight guard
- risk: low
- publishability: not_publishable

## Summary of Change

- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- added fast preflight for custom-frontend entry reachability:
  - default `BASE_URL` tightened to `http://localhost:8070` for current host runtime reachability
  - probe candidate origins derived from `BASE_URL` alias set
  - check `/login?db=...` and `/?db=...` with timeout
  - fail fast with structured reason:
    - `custom_frontend_entry_unreachable`
- preserved boundary:
  - no acceptance of native Odoo `/web` fallback path

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-890.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `native_odoo_surface_detected`
- `make verify.product.main_entry_convergence.v1`: FAIL
  - upstream contract/acceptance chain PASS
  - failed at host primary-entry gate with same `native_odoo_surface_detected`

## Key Evidence

- host smoke failed at native-surface guard:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs:521`
- main convergence failed with same root cause:
  - target `verify.portal.project_dashboard_primary_entry_browser_smoke.host`
- host runtime probe remains PASS:
  - browser runtime is healthy; blocker is entry routing into native Odoo frontend shell

## Risk Analysis

- iteration efficiency improved:
  - replaced long dashboard wait loops with quick environment-level classification
- architecture boundary preserved:
  - custom frontend only, no native frontend pass-through
- gate now explicitly rejects native Odoo fallback as invalid target
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-890.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-890.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-890.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated entry-routing fix batch:
  - keep `BASE_URL=http://localhost:8070` default for current runtime reachability
  - fix semantic entry routing so it lands on custom frontend scene shell instead of native Odoo shell
  - rerun host gate and then full `verify.product.main_entry_convergence.v1`
