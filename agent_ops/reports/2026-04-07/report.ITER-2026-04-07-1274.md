# ITER-2026-04-07-1274 Report

## Summary of change
- Implemented additive payment-ledger company isolation anchor.
- Updated model registration order to avoid pre-registration inherit failure.
- Changed files:
  - `addons/smart_construction_core/models/core/project_core.py`
  - `addons/smart_construction_core/models/core/__init__.py`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1274.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Deliverability impact
- Isolation anchor gate blocker removed for payment ledger object.
- `native_business_fact_isolation_anchor_verify` now passes with:
  - `payment.ledger:company_id,project_id`
- Native business-fact stage gate remains passable under real-role verification flow.

## Risk analysis
- Batch is high-risk lane but additive-only; no payment/settlement financial semantics changed.
- No ACL file, record-rule file, manifest, or frontend path touched.
- Import-order fix stays inside allowed module scope and only restores safe model loading sequence.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1274.yaml`
  - `git restore addons/smart_construction_core/models/core/__init__.py`
  - `git restore addons/smart_construction_core/models/core/project_core.py`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1274.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1274.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Continue requested main iteration lane:
  - project organization placement (`project.project` key owner fields + `sc.project.member`),
  - company/project isolation rule closure,
  - operability checks for project/task/budget/cost/payment/settlement.
