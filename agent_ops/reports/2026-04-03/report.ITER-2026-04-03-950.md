# ITER-2026-04-03-950

- status: FAIL
- mode: implement
- layer_target: Product Release Usability Proof
- module: runtime demo seed recovery
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-03-950.yaml`
- runtime actions:
  - executed `make db.demo.reset` to rebuild `sc_demo` with seed/demo modules.
  - verified seed lane with `make verify.demo.release.seed`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-950.yaml`: PASS
- `... make db.demo.reset`: PASS
- `... make verify.demo.release.seed DB_NAME=sc_demo`: PASS
- `... make verify.release.operator_surface.v1 DB_NAME=sc_demo`: FAIL
  - failure gate: `verify.product.scene_contract_guard`
  - failure: `project.initiation.enter failed: status=500 INTERNAL_ERROR`
  - trace_id: `54539fce4665`
- focused replay:
  - `... make verify.product.scene_contract_guard DB_NAME=sc_demo`: FAIL (same 500)

## Risk Analysis

- medium: environment seed gap is resolved, but a real backend runtime error now blocks release chain.
- stop condition triggered: `acceptance_failed`.

## Rollback Suggestion

- rerun environment baseline if needed:
  - `ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim make db.demo.reset`
- docs/task rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-03-950.yaml`
  - `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-950.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-03-950.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- publishability: `blocked`

## Next Iteration Suggestion

- open dedicated low-cost triage line for `verify.product.scene_contract_guard` 500 on `project.initiation.enter` (scan -> screen -> verify), then implement minimal backend fix.
