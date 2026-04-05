# ITER-2026-04-03-923

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: module-upgrade preflight guard orchestration
- risk: low
- publishability: publishable

## Summary of Change

- updated:
  - `scripts/mod/upgrade.sh`
- integration:
  - added pre-upgrade call to `scripts/ops/check_customer_seed_external_ids.sh`.
  - introduced mode switch `CUSTOMER_SEED_EXTERNAL_ID_GUARD`:
    - `off`: skip guard
    - `warn` (default): guard failure prints warning and continues
    - `strict`: guard failure blocks upgrade
  - guard auto-skips for non-target modules and `ENV=prod`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-923.yaml`: PASS
- `... CUSTOMER_SEED_EXTERNAL_ID_GUARD=warn make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`: PASS
  - preflight guard executed and PASS
  - module upgrade completed
- `... CUSTOMER_SEED_EXTERNAL_ID_GUARD=strict make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`: PASS
  - strict guard path executed and PASS
  - module upgrade completed

## Risk Analysis

- low risk: additive preflight only; default is non-blocking.
- safety gain:
  - strict mode now provides deterministic block gate for known seed external-id drift.

## Rollback Suggestion

- `git restore scripts/mod/upgrade.sh`
- `git restore agent_ops/tasks/ITER-2026-04-03-923.yaml`
- `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-923.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-03-923.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- optional: add Makefile alias targets for `customer-seed-guard.warn` / `customer-seed-guard.strict` to improve operator discoverability.
