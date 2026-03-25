# Edition Freeze Surface v1

## Released Scope

The first governed edition freeze surface covers:

- `construction.standard`
- `construction.preview`

## Freeze Contract

Edition freeze uses `edition_freeze_surface_v1` and records:

- current released policy
- released navigation
- released capabilities
- released scene bindings
- runtime meta and edition diagnostics

## Runtime Compatibility

- Delivery Engine v1 runtime resolution does not change
- released navigation semantics do not change
- standard delivery remains the default public surface
- preview remains a restricted release channel

## Rollback Evidence

Each active edition release snapshot keeps a rollback basis through `rollback_target_snapshot_id`.

This batch establishes:

- explicit freeze service
- replayable release surface payload
- deterministic rollback evidence

It does not yet switch runtime delivery to read from edition release snapshots.

## Guards

- `make verify.edition.freeze_surface_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.edition.release_snapshot_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.edition.rollback_evidence_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.edition_freeze.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo E2E_FALLBACK_LOGIN=demo_finance E2E_FALLBACK_PASSWORD=demo`
