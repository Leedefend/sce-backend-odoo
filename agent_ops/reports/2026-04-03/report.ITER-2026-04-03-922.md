# ITER-2026-04-03-922

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: runtime pre-upgrade guard
- risk: low
- publishability: publishable

## Summary of Change

- created:
  - `scripts/ops/check_customer_seed_external_ids.sh`
- capability:
  - checks duplicate seed logins in `res_users`.
  - checks missing/misaligned `smart_construction_custom` external-id mappings for existing seed users.
  - prints current seed login presence summary and returns explicit `PASS/FAIL`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-922.yaml`: PASS
- `ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim bash scripts/ops/check_customer_seed_external_ids.sh`: PASS
  - no duplicate logins
  - external-id mappings aligned

## Risk Analysis

- low risk: additive operational guard script only, no business behavior change.
- value:
  - catches external-id drift before module upgrade, reducing runtime collision failures.

## Rollback Suggestion

- `git restore scripts/ops/check_customer_seed_external_ids.sh`
- `git restore agent_ops/tasks/ITER-2026-04-03-922.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-922.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-922.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- optional follow-up: wire this guard into upgrade workflow pre-step (non-blocking warning mode first, then blocking mode).
