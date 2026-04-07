# ITER-2026-04-07-1266 Report

## Summary of change
- Fixed native project member sub-view validation blocker in `addons/smart_construction_core/views/core/project_views.xml` by adding missing domain dependency field in x2many tree:
  - added `<field name="company_id" invisible="1"/>` before `department_id/post_id`.
- This resolves Odoo validation error for `post_id` domain `[("company_id", "=", company_id)]` during module upgrade.

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1266.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- FAIL: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`
  - blocker moved forward from runtime 500 to explicit permission error:
  - `project.dashboard.enter` returns `403 PERMISSION_DENIED` on `project.project.stage_id` read for `User: 2`.

## Blocking points
- Current delivery blocker is now permission operability, not runtime unreachable / hook wiring / view validation.
- Exact blocker:
  - `product_project_flow_full_chain_execution_smoke`
  - `project.dashboard.enter` -> `PERMISSION_DENIED`
  - field: `stage_id`
  - required group: `Technical / Use Stages on Project`.

## Deliverability impact
- Improved:
  - Core module upgrade chain recovered; newly added project member factual fields can now materialize.
  - Runtime blocker moved from internal 500 to explicit actionable authorization gap.
- Not yet fully deliverable:
  - Native closure still blocked at project dashboard entry for real role user due stage-field permission.

## Risk analysis
- No forbidden path touched.
- Stop condition triggered by acceptance failure.
- Batch result: `FAIL`.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1266.yaml`
  - `git restore addons/smart_construction_core/views/core/project_views.xml`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1266.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1266.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Open a dedicated low-risk permission-operability recovery batch for `project.dashboard.enter` role user path, targeting role/user group supply (or equivalent read-path adjustment) for `project.project.stage_id`, then rerun stage gate.
