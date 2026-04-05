# ITER-2026-04-03-921

- status: PASS
- mode: implement
- layer_target: Product Release Usability Proof
- module: runtime data hygiene for customer seed
- risk: low
- publishability: publishable

## Summary of Change

- runtime DB cleanup only (`sc_prod_sim`), no repository source modifications.
- fixed root conflict by binding existing user `wutao` to missing external id:
  - `module`: `smart_construction_custom`
  - `name`: `user_sc_baosheng_wutao`
  - `model`: `res.users`
  - `res_id`: existing user id in `sc_prod_sim`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-03-921.yaml`: PASS
- SQL acceptance check (target logins count): PASS
  - all target logins present with count `1`
- `ENV=test ... MODULE=smart_construction_core DB_NAME=sc_prod_sim CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core make mod.upgrade`: PASS
  - no duplicate-login failure in `customer_users.xml`

## Key Evidence

- before fix:
  - `wutao` existed without smart_construction_custom external id mapping
- after fix:
  - `ir_model_data` contains `smart_construction_custom.user_sc_baosheng_wutao`
  - upgrade path passes on `sc_prod_sim`

## Risk Analysis

- low code risk: repo source unchanged
- medium runtime caution:
  - cleanup modifies production-sim data dictionary mapping; action is minimal and scoped to one user external-id bridge.

## Rollback Suggestion

- runtime rollback option:
  - remove inserted `ir_model_data` row for `smart_construction_custom.user_sc_baosheng_wutao` if needed
  - or restore `sc_prod_sim` DB snapshot
- governance rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-03-921.yaml`
  - `git restore agent_ops/reports/2026-04-03/report.ITER-2026-04-03-921.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-03-921.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- publishability: `publishable`

## Next Iteration Suggestion

- open optional low-risk batch to codify a pre-upgrade guard script that checks missing `ir_model_data` mappings for known seed logins before module upgrade.
