# Release Audit Trail Surface v1

## Status

`release audit trail surface governed`

## Scope

Fold `sc.release.action`, `edition release snapshot`, `snapshot lineage`, `rollback evidence`, and runtime released snapshot diagnostics into one exportable audit surface.

## Surface

- service: `addons/smart_core/delivery/release_audit_trail_service.py`
- runtime additive diagnostics:
  - `edition_runtime_v1.diagnostics.released_snapshot_lineage`
  - `edition_runtime_v1.diagnostics.release_audit_trail_summary`
- artifacts:
  - `artifacts/backend/release_audit_surface_guard.json`
  - `artifacts/backend/release_audit_lineage_consistency_guard.json`
  - `artifacts/backend/release_audit_runtime_consistency_guard.json`

## Guarantees

- audit view is built from release truth, not ad hoc runtime state
- active released snapshot remains unique per edition product
- rollback evidence remains resolvable from the audit surface
- runtime diagnostics explain which released snapshot was hit

## Gate

- `make verify.release.audit_surface_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.audit_lineage_consistency_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim`
- `make verify.release.audit_runtime_consistency_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- `make verify.release.audit_trail.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo E2E_FALLBACK_LOGIN=demo_finance E2E_FALLBACK_PASSWORD=demo`
