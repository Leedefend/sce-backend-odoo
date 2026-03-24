# Delivery Engine v1 Contract

## Goal

Freeze a single release runtime that controls:

- visible product navigation
- released scene exposure
- released capability exposure

## Runtime Output

`system.init.data.delivery_engine_v1`

Required top-level fields:

- `contract_version`
- `source`
- `product_key`
- `role_code`
- `nav`
- `scenes`
- `capabilities`
- `product_policy`
- `meta`

## Product Policy

Current frozen policy:

- `product_key = construction.standard`

Released menu keys:

- `release.fr1.project_intake`
- `release.fr2.project_flow`
- `release.fr3.cost_tracking`
- `release.fr4.payment_tracking`
- `release.fr5.settlement_summary`
- `release.my_work`

Released scene keys:

- `projects.intake`
- `project.management`
- `cost`
- `payment`
- `settlement`
- `my_work.workspace`

Released capability keys:

- `delivery.fr1.project_intake`
- `delivery.fr2.project_flow`
- `delivery.fr3.cost_tracking`
- `delivery.fr4.payment_tracking`
- `delivery.fr5.settlement_summary`
- `delivery.my_work.workspace`

## Compatibility Rule

`release_navigation_v1` is a compatibility projection from `delivery_engine_v1.nav`.
It must not drift independently.

## Verification

- menu guard:
  - `make verify.product.delivery_menu_integrity_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- scene guard:
  - `make verify.product.delivery_scene_integrity_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- product policy guard:
  - `make verify.product.delivery_policy_guard ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- unified gate:
  - `make verify.release.delivery_engine.v1 ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
