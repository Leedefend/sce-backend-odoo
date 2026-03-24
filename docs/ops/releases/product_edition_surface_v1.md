# Product Edition Surface v1

## Scope

Edition-aware released surface for:

- `construction.standard`
- `construction.preview`

## Guarantees

- standard and preview have separate policy records
- each edition has its own `scene_version_bindings`
- preview scene binding must not mutate standard edition delivery
- delivery runtime resolves edition identity and edition-specific bindings

## Guard Baseline

- `make verify.product.edition_policy_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.edition_binding_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.edition_surface.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`

## Non-Goals

- no navigation split
- no FR-1 to FR-5 semantic changes
- no new edition UI selector
