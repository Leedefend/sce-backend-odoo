# Verify Plan - Frontend Strict Contract Consumption v1

## Verify Targets
- `verify.frontend.contract.strict.core_scenes`
- `verify.scene.surface.contract`
- `verify.scene.action_surface.contract`
- `verify.product.projection.contract.core_scenes`
- `verify.frontend.no_hardcoded_core_scene_registry`

## Pilot Scope
- `workspace.home`
- `finance.payment_requests`
- `risk.center`
- `project.management`

## Verification Items

### 1) Strict Mode Source Verification
- Assert strictness source is backend-only:
  - `runtime_policy.strict_contract_mode=true` OR
  - `scene_tier=core`
- Assert frontend has no hardcoded core-scene registry as strict source.

### 2) Surface Contract Verification
- For pilot scenes, validate presence of:
  - `surface.kind`
  - `surface.intent.title`
  - `surface.intent.summary`
  - `view_modes[]`
  - `sections` (if declared)
- In strict mode, missing surface contract shows explicit contract-missing state.

### 3) Action Surface Verification
- Validate `action_surface.groups` structure and ordering in runtime payload.
- In strict mode, ActionView does not execute keyword grouping heuristics.

### 4) Projection Contract Verification
- Validate `projection.summary_items`, `projection.overview_strip`, and `projection.group_summary` on pilot scenes.
- In strict mode, frontend does not execute `listSemanticKind/listSummaryItems/ledgerOverviewItems` business inference paths.

### 5) Mutation + Refresh Runtime Verification
- Validate scene actions with `mutation` route to correct intent handlers.
- Validate `refresh_policy.on_success` triggers scene/workbench projection refresh.

## Suggested Commands
- Frontend lint (targeted):
  - `pnpm exec eslint src/views/ActionView.vue src/views/HomeView.vue src/pages/ContractFormPage.vue src/app/contractStrictMode.ts src/app/resolvers/sceneReadyResolver.ts src/app/pageContract.ts src/utils/semantic.ts`
- Backend targeted tests:
  - `odoo tests`: `addons/smart_core/tests/test_scene_runtime_contract_chain.py`
  - `odoo tests`: `addons/smart_construction_core/tests/test_risk_action_execute_backend.py`

## Pass Criteria
- All pilot scenes pass strict source checks.
- No critical frontend heuristic branch executes in strict mode for pilot scenes.
- Mutation and refresh chain succeeds for risk/payment sample actions.
- Lint and targeted tests pass.
