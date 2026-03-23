# Payment Slice Verification Matrix

## Scope

- slice: `execution/cost -> payment entry -> payment list -> payment summary`
- stage: `Prepared`
- excluded: `contract terms / approval / invoice / tax / settlement / cost recalculation`

## Required Verify

1. `make verify.product.payment_entry_contract_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
2. `make verify.product.payment_list_block_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
3. `make verify.product.payment_summary_block_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
4. `make verify.product.project_flow.execution_payment DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
5. `make verify.portal.payment_slice_browser_smoke.host BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
6. `make verify.release.payment_slice_prepared ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
7. `make verify.release.payment_slice_freeze ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## Expected Artifacts

- `artifacts/backend/product_payment_entry_contract_guard.json`
- `artifacts/backend/product_payment_list_block_guard.json`
- `artifacts/backend/product_payment_summary_block_guard.json`
- `artifacts/backend/product_project_flow_execution_payment_smoke.json`
- `artifacts/codex/payment-slice-browser-smoke/<timestamp>/summary.json`

## Contract Coverage

- `payment.enter`
- `payment.block.fetch`
- `payment.record.create`
- `execution -> payment`
- `cost -> payment`

## Prepared Pass Rule

- all contract guards pass
- execution -> payment flow smoke pass
- browser smoke pass
- no expansion into approval / settlement / contract management
- freeze gate pass
