# Scene Version Surface v1

## Goal

Upgrade released scenes from runtime-only contract output to version-bindable product assets.

## Included Surface

- `projects.intake`
- `project.management`
- `cost`
- `payment`
- `settlement`
- `my_work.workspace`

## Runtime Rules

- Released scene snapshots are stored in `sc.scene.snapshot`
- Stable product delivery remains governed by `sc.product.policy`
- Active scene asset version is selected by `scene_version_bindings`
- Delivery runtime prefers bound snapshot contract over rebuilt fallback contract

## Current Default Binding

For `construction.standard`, all released scenes are bound to:

- `version = v1`
- `channel = stable`

## Verification

- `make verify.scene.freeze_snapshot_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.replication_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.version_binding_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.scene_asset.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`

## Non-Goals

- no new scene admin UI
- no legacy scene governance migration
- no FR-1 to FR-5 behavior change
- no menu storage redesign
