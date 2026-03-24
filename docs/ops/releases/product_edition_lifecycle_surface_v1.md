# Product Edition Lifecycle Surface v1

## Released Surface

This release surface governs edition lifecycle for:

- `construction.standard`
- `construction.preview`

## Release Rules

- standard remains the default released delivery surface
- preview is a restricted release channel
- preview must not pollute standard runtime delivery
- runtime fallback must remain deterministic and auditable

## Runtime Contract Expectations

`delivery_engine_v1` now exposes edition lifecycle diagnostics through `product_policy.edition_diagnostics` and `meta.edition_diagnostics`.

Minimum diagnostics:

- `requested_product_key`
- `requested_edition_key`
- `resolved_product_key`
- `resolved_edition_key`
- `policy_state`
- `access_level`
- `access_allowed`
- `fallback_reason`

## Access Policy

- `construction.standard`
  - public
- `construction.preview`
  - role restricted
  - allowed roles: `pm`, `executive`

## Promotion Policy

Edition promotion must use the governed transition path:

- `draft -> ready`
- `ready -> preview`
- `preview -> stable`

Rollback must reactivate a previous stable edition under the same `base_product_key`.

## Guards

- `make verify.edition.lifecycle_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.edition.access_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.edition.promotion_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.edition_lifecycle.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`

## Out of Scope

- no new edition admin UI
- no visual edition selector
- no reopened FR-1 to FR-5 business logic
- no released navigation rewrite
