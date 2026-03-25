# Release Approval Policy Surface v1

## Status

`release action policy and minimal approval governed`

## Scope

Upgrade release orchestration from executable flow to policy-controlled release control:

- action executor policy
- approval requirement
- approver policy
- pending approval state
- controlled self-approval for release admins

## Surface

- service: `addons/smart_core/delivery/release_approval_policy_service.py`
- model: `addons/smart_core/models/release_action.py`
- orchestration: `addons/smart_core/delivery/release_orchestrator.py`

## Runtime Guarantees

- preview promote does not require approval
- standard promote requires approval unless a release admin self-approves
- rollback cannot be executed by `pm`
- release action records keep approval fields for later audit/export

## Gate

- `make verify.release.policy_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.approval_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.approval.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo E2E_FALLBACK_LOGIN=demo_finance E2E_FALLBACK_PASSWORD=demo`
