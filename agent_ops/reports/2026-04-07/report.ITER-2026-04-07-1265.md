# ITER-2026-04-07-1265 Report

## Summary of change
- Patched `addons/smart_construction_core/__init__.py` to expose smart_core runtime provider hooks at addon root, including:
  - `smart_core_build_project_dashboard_service`
  - `smart_core_build_project_execution_service`
  - `smart_core_build_project_plan_bootstrap_service`
  - `smart_core_build_cost_tracking_service`
  - `smart_core_build_payment_slice_service`
  - `smart_core_build_settlement_slice_service`
  - and related portal/capability hooks.
- Purpose: recover `project.dashboard.enter` runtime hook lookup path from extension loader.

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1265.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_custom DB_NAME=sc_prod_sim`
- FAIL: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`
  - first run: `project.dashboard.enter` still 500 (`missing extension hook result`), because runtime process had not reloaded.
  - after `ENV=prod.sim ENV_FILE=.env.prod.sim make restart`, stage gate moved forward but hit transient strict runtime unreachable once (expected strict behavior), then rerun progressed.
  - rerun then failed at `project.project api.data list` with DB schema mismatch (`project_manager_user_id` column missing).
- FAIL (additional recovery attempt): `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
  - blocked by existing view validation error in `addons/smart_construction_core/views/core/project_views.xml`:
    - `Field 'company_id' used in domain of python field 'post_id' ... must be present in view but is missing.`

## Blocking points
- Active blocker shifted to module upgrade integrity:
  - `smart_construction_core` upgrade cannot complete due project form view validation error.
- Because upgrade is blocked, newly added project member fields are not fully materialized in DB, causing downstream `api.data` 500 and preventing full stage-gate completion.

## Deliverability impact
- Positive:
  - Runtime hook exposure patch is in place and aligned with extension loader contract.
- Not yet deliverable:
  - Native business-fact stage gate still FAIL due pre-existing `project_views.xml` validation blocker.

## Risk analysis
- No forbidden path touched in this batch.
- Stop condition triggered by acceptance failure.
- Batch result: `FAIL`.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1265.yaml`
  - `git restore addons/smart_construction_core/__init__.py`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1265.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1265.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Open dedicated low-risk recovery batch to fix `addons/smart_construction_core/views/core/project_views.xml` validation issue, complete `smart_construction_core` upgrade, then rerun `verify.native.business_fact.stage_gate` to confirm dashboard runtime closure end-to-end.
