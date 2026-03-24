# Scene Asset Lifecycle Surface v1

## Scope

Released scene lifecycle governance for:

- `projects.intake`
- `project.management`
- `cost`
- `payment`
- `settlement`
- `my_work.workspace`

## Governed Surface

- `sc.scene.snapshot.state`
- `scene_promotion_service`
- `scene_version_bindings`
- `delivery_engine_v1` snapshot resolution and fallback diagnostics

## Guard Baseline

- `make verify.scene.freeze_snapshot_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.replication_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.version_binding_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.lifecycle_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.promotion_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.scene.active_uniqueness_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.scene_asset.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`

## Runtime Compatibility

- released navigation semantics do not change
- FR-1 to FR-5 semantics do not reopen
- non-bindable snapshots do not break delivery runtime; they trigger fallback with diagnostics
