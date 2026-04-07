# ITER-2026-04-07-1277 Report

## Summary of change
- Completed dedicated high-risk permission-governance implementation for
  project-member rule binding on core business objects.
- Updated `addons/smart_construction_core/security/sc_record_rules.xml` with
  additive domains that bind access to:
  - project key role facts (`project_manager_user_id`, `technical_lead_user_id`,
    `business_lead_user_id`, `cost_lead_user_id`, `finance_contact_user_id`)
  - project member carrier fact (`project_member_ids.user_id`)
  - task assignee fact (`project.task.user_ids`) for task visibility.
- Added verification script:
  - `scripts/verify/native_business_fact_project_member_rule_binding_verify.py`

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1277.yaml`
- PASS: `python3 scripts/verify/native_business_fact_project_member_rule_binding_verify.py`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Deliverability impact
- Access boundaries for project/task/budget/cost/payment/settlement are now
  fact-bound to project organization modeling closure output.
- Reduces dependency on legacy follower-based visibility for targeted objects.
- Keeps stage-gate operability and real-role flow pass status.

## Risk analysis
- High-risk lane executed under dedicated `permission-governance` task scope.
- No `ir.model.access.csv`, manifest, frontend, or financial semantics changes.
- Changes are additive domain replacements within approved `security` target.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1277.yaml`
  - `git restore addons/smart_construction_core/security/sc_record_rules.xml`
  - `git restore scripts/verify/native_business_fact_project_member_rule_binding_verify.py`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1277.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1277.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Add negative-role runtime acceptance (same-company non-member denial proofs)
  as dedicated verify batch, then tighten any residual non-target domains.
