# prod-sim Isolation Verification Runbook

This runbook verifies whether `prod-sim` is properly isolated from the default development environment.

## When to use
- Full pre-release environment verification
- Suspected `prod-sim` drift (modules/data/runtime mismatch)
- Fast daily regression checks during integration work

## Prerequisites
- Non-production execution context: `ENV=test` + `.env.prod.sim`
- Docker is available and `sc-backend-odoo-prod-sim` can start
- Verification credential is available: `svc_e2e_smoke/demo`

## Commands
- Full isolation verification (resets `sc_prod_sim`):
  - `make verify.prod.sim.isolation`
- Quick isolation verification (no reset, daily use):
  - `make verify.prod.sim.isolation.quick`

## Target differences
- `verify.prod.sim.isolation`
  - Pipeline: `up -> demo.reset -> odoo.recreate -> wait.odoo.ready -> verify.delivery.simulation.ready`
  - Use case: pre-release and post-drift strong verification
- `verify.prod.sim.isolation.quick`
  - Pipeline: `up -> wait.odoo.ready -> verify.delivery.simulation.ready`
  - Use case: fast daily health regression

## Outputs and pass criteria
- PASS signal: command ends with `PASS`
- Report files:
  - `docs/ops/audit/delivery_simulation_report.md`
  - `artifacts/backend/delivery_simulation_report.json`

## Common issues
- Port conflicts (for example `18069`/`80`): stop conflicting containers and retry
- Login failure: verify credential `svc_e2e_smoke/demo`
- Early connection reset after restart: retry `quick`, or run full target once
