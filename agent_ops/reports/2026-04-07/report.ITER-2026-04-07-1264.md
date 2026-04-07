# ITER-2026-04-07-1264 Report

## Summary of change
- Extended `project.project` with key project-position fields:
  - `project_manager_user_id`
  - `technical_lead_user_id`
  - `business_lead_user_id`
  - `cost_lead_user_id`
  - `finance_contact_user_id`
- Reused existing `project.responsibility` as project member factual carrier and added member facts:
  - `project_role_code`, `department_id`, `post_id`, `is_primary`, `active`, `date_start`, `date_end`, `note`
- Added native project form entry for project member maintenance:
  - `project_member_ids` tree on project form.
- Added minimal business linkage by syncing project followers from:
  - creator, key-position users, explicit members, and users implied by member post.
- Added docs:
  - `docs/ops/project_member_role_design_v1.md`
  - `docs/ops/project_member_role_acceptance_v1.md`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1264.yaml`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_custom DB_NAME=sc_prod_sim`
- FAIL: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`
  - PASS sub-check: role operability blocker gate
  - FAIL sub-check: native closure full-chain (`project.dashboard.enter` runtime 500)

## Blocking points
- Current active blocker remains runtime closure path:
  - `product_project_flow_full_chain_execution_smoke` fails at `project.dashboard.enter` with `INTERNAL_ERROR`.

## Deliverability impact
- Improved factual deliverability:
  - Project is no longer a staffing-empty shell; native project member facts are maintainable.
  - Project/task visibility has member-fact linkage through follower sync baseline.
- Not fully deliverable yet:
  - Admin full closure chain still blocked by dashboard runtime 500.

## Risk analysis
- No forbidden path touched.
- Stop condition triggered by acceptance failure.
- Batch result: `FAIL`.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1264.yaml`
  - `git restore addons/smart_construction_core/models/core/project_core.py`
  - `git restore addons/smart_construction_core/views/core/project_views.xml`
  - `git restore docs/ops/project_member_role_design_v1.md`
  - `git restore docs/ops/project_member_role_acceptance_v1.md`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1264.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1264.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Open dedicated runtime diagnosis batch for `project.dashboard.enter` 500 and rerun blocker-focused stage gate.
