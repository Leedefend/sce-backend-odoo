# Release Navigation Contract

## Goal

Freeze the release-grade sidebar navigation as a product contract, not as a raw scene tree.

## Scope

This contract governs the main sidebar surface for the PM demo role in the released shell.

It does not redefine FR-1 to FR-5 business semantics.
It only governs how released product slices are exposed to the user.

## Release Navigation Surface

The released PM sidebar must expose:

### Group: 已发布产品

- `FR-1 项目立项`
- `FR-2 项目推进`
- `FR-3 成本记录`
- `FR-4 付款记录`
- `FR-5 结算结果`

### Group: 工作辅助

- `我的工作`

## Entry Strategy

- `FR-1 项目立项`
  - direct route: `/s/projects.intake`
- `FR-2 ~ FR-5`
  - product entry route: `/release/<productKey>`
  - the route may require project context, but the sidebar still exposes the product entry explicitly
- `我的工作`
  - direct route: `/my-work`

## Forbidden Main Sidebar Exposure

The released sidebar must not use these as the primary user-facing IA:

- raw Odoo root menu trees
- technical scene names such as:
  - `projects.intake`
  - `projects.list`
  - `projects.ledger`
  - `project.management`
- arbitrary mixed scene dumps

## Runtime Ownership

- backend owner:
  - `addons/smart_core/core/release_navigation_contract_builder.py`
- startup payload owner:
  - `addons/smart_core/core/system_init_payload_builder.py`
  - `addons/smart_core/handlers/system_init.py`
- frontend consumer:
  - `frontend/apps/web/src/stores/session.ts`
  - `frontend/apps/web/src/layouts/AppShell.vue`

## Verification

- contract guard:
  - `make verify.product.release_navigation_contract_guard DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- browser smoke:
  - `make verify.portal.release_navigation_browser_smoke.host BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`
- unified gate:
  - `make verify.release.navigation.surface ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=demo_pm E2E_PASSWORD=demo`

The guard must assert:

- `role_surface.role_code == pm`
- `release_navigation_v1` exists in live `system.init`
- group labels are fixed
- release leaf labels are fixed
- real browser sidebar text contains the same released product labels

## Conclusion

Release navigation is now a governed release surface.
If the sidebar falls back to scene-first output again, it is a contract regression.
