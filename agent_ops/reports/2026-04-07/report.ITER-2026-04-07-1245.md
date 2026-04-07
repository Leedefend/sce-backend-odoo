# ITER-2026-04-07-1245 Report

## Summary of change
- Updated `addons/smart_construction_custom/data/customer_users.xml` to set explicit default password `demo` for target real users:
  - `user_sc_baosheng_wutao`
  - `user_sc_baosheng_xiaohuijiu`
  - `user_sc_baosheng_shuiwujingbanren`
  - `user_sc_baosheng_wennan`
- Attempted one module upgrade as requested.

## Changed files
- `agent_ops/tasks/ITER-2026-04-07-1245.yaml`
- `addons/smart_construction_custom/data/customer_users.xml`
- `agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1245.md`
- `agent_ops/state/task_results/ITER-2026-04-07-1245.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1245.yaml`
- FAIL: `CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=sc_demo make mod.upgrade`
  - failure reason: duplicate company seed during module data load
  - key error: `psycopg2.errors.UniqueViolation` on `res_company_name_uniq`
  - parse context: `smart_construction_custom/data/customer_company_departments.xml` record `company_sc_baosheng`
- As acceptance failed, real-user stage gate rerun is not executed in this batch.

## Risk analysis
- Stop condition triggered (`acceptance_failed`).
- Current blocker is module upgrade data conflict unrelated to password-field patch itself.

## Rollback suggestion
- Revert patch if needed:
  - `git restore addons/smart_construction_custom/data/customer_users.xml`
- Or fix upgrade blocker first (deduplicate/guard existing company seed path), then re-run upgrade and gate.

## Next iteration suggestion
- Open dedicated low-risk screen batch for `smart_construction_custom` upgrade idempotency conflict in `customer_company_departments.xml`.
- After resolving that blocker, rerun:
  - `CODEX_NEED_UPGRADE=1 MODULE=smart_construction_custom DB_NAME=<target_db> make mod.upgrade`
  - real-user `make verify.native.business_fact.stage_gate`
