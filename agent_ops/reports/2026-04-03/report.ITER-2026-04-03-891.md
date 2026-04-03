# ITER-2026-04-03-891

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: host login-entry preflight contract
- risk: low
- publishability: not_publishable

## Summary of Change

- updated:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- hardened custom-login contract preflight:
  - preflight now validates `/login?db=...` contract first
  - requires non-error HTTP status and login-form signatures
  - detects Odoo website 404 signature and emits:
    - `custom_login_route_missing`
- still preserves custom-frontend-only boundary:
  - no native Odoo `/web` fallback acceptance

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-891.yaml`: PASS
- `make verify.portal.project_dashboard_primary_entry_browser_smoke.host`: FAIL
  - `custom_frontend_entry_unreachable: custom_login_route_missing`
- `make verify.product.main_entry_convergence.v1`: FAIL
  - upstream contract/management chain PASS
  - host gate fails with same `custom_login_route_missing`

## Key Evidence

- host gate fails at strict preflight line:
  - `scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs:650`
- failure indicates current `BASE_URL` login entry does not satisfy custom login contract
- runtime probe still PASS:
  - browser runtime healthy, blocker is entry route contract

## Risk Analysis

- verification signal quality improved:
  - from vague timeouts -> precise route-contract mismatch
- architecture boundary preserved:
  - native frontend remains invalid target
- publishability remains `not_publishable`

## Rollback Suggestion

- `git restore scripts/verify/project_dashboard_primary_entry_browser_smoke.mjs`
- `git restore agent_ops/tasks/ITER-2026-04-03-891.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-891.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-891.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `not_publishable`

## Next Iteration Suggestion

- open dedicated environment-route batch:
  - locate and freeze the real custom frontend login entry URL (not Odoo website 404 page)
  - bind that URL into host smoke defaults
  - rerun host gate and then full convergence gate
