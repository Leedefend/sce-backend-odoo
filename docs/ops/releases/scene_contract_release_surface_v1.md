# Scene Contract Release Surface v1

## Released Scenes

Frozen release surface:

- FR-1: `projects.intake`
- FR-2: `project.dashboard`
- FR-2: `project.plan_bootstrap`
- FR-2: `project.execution`
- FR-3: `cost.tracking`
- FR-4: `payment`
- FR-5: `settlement`
- Utility: `my_work.workspace`

## Runtime Standard

Released scene contract field:

- `scene_contract_standard_v1`

Current sources:

- `delivery_engine_v1.scenes[*].scene_contract_standard_v1`
- `*.enter -> data.scene_contract_standard_v1`
- `page.contract -> data.page_contract.scene_contract_standard_v1`

## Field Freeze

Released surface fields:

- top-level `contract_version`
- `identity`
- `target`
- `state`
- `page`
- `actions`
- `governance`

Compatibility-retained but not release-defining:

- `scene_label`
- `summary`
- `state_fallback_text`
- `runtime_fetch_hints`
- `page_orchestration_v1`
- `scene_contract_v1`

## Verification

- scene contract guard:
  - `make verify.product.scene_contract_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- release gate:
  - `make verify.release.delivery_engine.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`

Artifacts:

- `artifacts/backend/product_scene_contract_guard.json`
- `artifacts/backend/product_scene_contract_guard.md`

## Batch Conclusion

This batch standardizes released scenes as a governed contract surface while keeping:

- FR-1 to FR-5 frozen
- Release Navigation governed
- Delivery Engine v1 governed

It does not reopen business semantics and does not attempt full scene-provider unification.
