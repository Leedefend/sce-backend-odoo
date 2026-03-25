# Release Operator Surface v1

## Status

`release operator surface governed`

## Scope

This surface upgrades release delivery from backend-only control to a minimal operable surface:

- view current release state
- view pending approval actions
- view release history
- request promote
- approve action
- execute rollback

## Runtime Rules

- every mutate path goes through release policy
- every mutate path goes through release orchestrator
- every mutate path remains in release audit trail
- released navigation semantics do not change

## Gate

- `make verify.release.operator_surface_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.operator_orchestration_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.portal.release_operator_surface_browser_smoke.host ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- `make verify.release.operator_surface.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo E2E_FALLBACK_LOGIN=demo_finance E2E_FALLBACK_PASSWORD=demo`
