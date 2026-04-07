# ITER-2026-04-07-1275 Report

## Summary of change
- Kept `ITER-1275` mainline and completed minimal enhancement for
  "项目组织事实建模闭环 v1".
- Project key role facts on `project.project` are now independent fields
  (removed related-alias dependency for manager/business/cost project-role fields).
- Extracted project member carrier model into dedicated file:
  - `addons/smart_construction_core/models/core/project_member.py`
- Registered member model loader:
  - `addons/smart_construction_core/models/core/__init__.py`
- Added project-organization closure verifier and hooked into stage gate:
  - `scripts/verify/native_business_fact_project_org_closure_verify.py`
  - `Makefile`
- Added runtime acceptance verify for native form visibility + member entry +
  persistence:
  - `scripts/verify/native_business_fact_project_org_native_form_persistence_verify.py`
- Updated design/acceptance docs with deferred ACL/rule binding note.

## Blocking points
- Initial persistence verify attempt failed due argument shape error in JSON-RPC
  `call_kw` create/write flow (`TypeError: unhashable type: 'list'`).

## Fixes
- Corrected JSON-RPC call argument shapes for create/write/read/unlink in
  persistence verify script.
- Added safe cleanup guards to avoid teardown failure masking.

## Verification result
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-07-1275.yaml`
- PASS: `python3 scripts/verify/native_business_fact_project_org_closure_verify.py`
- PASS: `CODEX_NEED_UPGRADE=1 ENV=prod.sim ENV_FILE=.env.prod.sim make mod.upgrade MODULE=smart_construction_core DB_NAME=sc_prod_sim`
- PASS: `DB_NAME=sc_prod_sim E2E_BASE_URL=http://localhost:18069 ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo python3 scripts/verify/native_business_fact_project_org_native_form_persistence_verify.py`
- PASS: `ROLE_OWNER_LOGIN=wutao ROLE_OWNER_PASSWORD=demo ROLE_PM_LOGIN=xiaohuijiu ROLE_PM_PASSWORD=demo ROLE_FINANCE_LOGIN=shuiwujingbanren ROLE_FINANCE_PASSWORD=demo ROLE_EXECUTIVE_LOGIN=wennan ROLE_EXECUTIVE_PASSWORD=demo E2E_BASE_URL=http://localhost:18069 make verify.native.business_fact.stage_gate DB_NAME=sc_prod_sim`

## Deliverability uplift
- Native project form has key role fields and member maintenance entry verified.
- Runtime verify confirms create/write/read persistence for project role fields
  and member carrier linkage.
- This iteration improves native business-fact deliverability from
  "structure present" to "modeling closure v1 with persistence evidence".

## Risk analysis
- No ACL/record-rule/manifest/frontend path changed.
- Payment/settlement financial semantics unchanged.
- Remaining deferred scope is explicit: permission binding based on member facts
  to be handled in next dedicated iteration.

## Rollback suggestion
- If rollback required:
  - `git restore agent_ops/tasks/ITER-2026-04-07-1275.yaml`
  - `git restore addons/smart_construction_core/models/core/__init__.py`
  - `git restore addons/smart_construction_core/models/core/project_core.py`
  - `git restore addons/smart_construction_core/models/core/project_member.py`
  - `git restore scripts/verify/native_business_fact_project_org_closure_verify.py`
  - `git restore scripts/verify/native_business_fact_project_org_native_form_persistence_verify.py`
  - `git restore Makefile`
  - `git restore docs/ops/project_member_role_design_v1.md`
  - `git restore docs/ops/project_member_role_acceptance_v1.md`
  - `git restore agent_ops/reports/2026-04-07/report.ITER-2026-04-07-1275.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-07-1275.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- Start dedicated permission-binding iteration:
  - bind project/task/budget/cost/payment/settlement visibility rules to
    project-member facts,
  - keep additive rule matrix and real-role operability checks.
