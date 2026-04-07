# ITER-2026-04-07-1281 Report

## Summary of change
- Implemented dedicated outsider seed user path for strict fixed-user deny matrix.
- Added fixed outsider user in customer seed:
  - `addons/smart_construction_custom/data/customer_users.xml`
  - login: `outsider_seed`
  - company: `company_sc_baosheng`
  - groups: `base.group_user` only
  - password seed: `demo`
- Added canonical authorization write for outsider seed to enforce deterministic
  password/groups on upgrades:
  - `addons/smart_construction_custom/data/customer_user_authorization.xml`
- Updated matrix verify to support strict outsider deny mode:
  - `scripts/verify/native_business_fact_fixed_user_matrix_verify.py`
  - env flag: `STRICT_OUTSIDER_DENY=true`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1281.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_custom DB_NAME=sc_prod_sim`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_OUTSIDER_LOGIN=outsider_seed ROLE_OUTSIDER_PASSWORD=demo STRICT_OUTSIDER_DENY=true python3 scripts/verify/native_business_fact_fixed_user_matrix_verify.py`

## Deliverability impact
- Strict fixed-user outsider deny matrix becomes reproducible and passes with
  seeded outsider identity.
- Acceptance dossier now has:
  - fixed real-user allow matrix
  - strict fixed outsider deny matrix.

## Risk analysis
- No ACL/record-rule/manifest/frontend edits in this batch.
- Additive seed-only change, scoped to customer data + verify script.

## Rollback suggestion
- `git restore agent_ops/tasks/ITER-2026-04-07-1281.yaml`
- `git restore addons/smart_construction_custom/data/customer_users.xml`
- `git restore addons/smart_construction_custom/data/customer_user_authorization.xml`
- `git restore scripts/verify/native_business_fact_fixed_user_matrix_verify.py`
- `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1281.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-07-1281.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Run one consolidated acceptance bundle report that merges:
  - runtime reachable status,
  - project organization fact closure,
  - member-bound rule closure,
  - strict outsider deny matrix evidence.
