# Release Operator Read Model v1

## Status

`release operator read model governed`

## Scope

This read layer standardizes operator reads for:

- current release state
- pending approval queue
- release history summary
- available operator actions

## Rules

- read model is the preferred source for operator surface and operator page
- read model stays read-only
- mutate actions still go through release policy + orchestrator + audit trail
- existing `release_operator_surface_v1` semantics do not regress

## Gate

- `make verify.release.operator_read_model_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.portal.release_operator_read_model_browser_smoke.host ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- `make verify.release.operator_read_model.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo E2E_FALLBACK_LOGIN=demo_finance E2E_FALLBACK_PASSWORD=demo`
