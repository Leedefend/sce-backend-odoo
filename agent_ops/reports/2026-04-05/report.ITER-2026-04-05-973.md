# ITER-2026-04-05-973

- status: FAIL
- mode: implement
- layer_target: Delivery Simulation Runtime Alignment
- module: prod-sim module footprint and customer user baseline
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-973.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-973.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-973.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - uninstalled `smart_construction_demo` from `sc_prod_sim` runtime.
  - restarted prod-sim stack and reloaded `smart_construction_custom` via `make mod.upgrade`.
  - customer seed user external-id guard returned PASS after reload.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-973.yaml`: PASS
- `... make restart` (`DB_NAME=sc_prod_sim`): PASS
- `module state check`: PASS
  - `smart_construction_demo=uninstalled`
  - `smart_construction_custom=installed`
- `... make mod.upgrade MODULE=smart_construction_custom ...`: PASS
- `... make guard.customer_seed_external_ids.strict`: PASS
- `... make verify.release.execution_protocol.v1`: FAIL
  - failure point: `verify.product.delivery_menu_integrity_guard`
  - detail: `E2E_LOGIN=svc_e2e_smoke` login returned 401 (`AUTH_REQUIRED`, 用户名或密码错误)

## Risk Analysis

- medium: target runtime objective (remove demo + import customer users) is achieved,
  but release execution protocol cannot pass with the current verification account
  lane because `svc_e2e_smoke` is unavailable under the new runtime baseline.

## Rollback Suggestion

- runtime rollback option A: restore `sc_prod_sim` from pre-batch DB snapshot.
- runtime rollback option B: reinstall demo module for temporary compatibility
  (`MODULE=smart_construction_demo ... make mod.install DB_NAME=sc_prod_sim`).
- repo rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-05-973.yaml`
  - `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-973.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-05-973.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop_condition: `acceptance_failed`
- publishability: `blocked`

## Next Iteration Suggestion

- open dedicated runtime credential-lane task to align release verification login
  account with customer-delivery baseline (replace or provision `svc_e2e_smoke`
  equivalent account) and rerun `make verify.release.execution_protocol.v1`.
