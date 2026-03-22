# Orchestration Migration Status v1

## Scope
- objective: move scene entry/block/action contract assembly out of industry-local ownership and into platform-owned orchestration carriers
- principle: business-truth services stay in domain modules, orchestration carriers move into `addons/smart_core/orchestration`, frontend consumes contract only

## Platformized Scenes

### `project.execution`
- carrier owner: `addons/smart_core/orchestration/project_execution_scene_orchestrator.py`
- handler import path: `addons/smart_construction_core/handlers/project_execution_*`
- status: `platformized`
- notes:
  - entry/runtime contract assembly is platform-owned
  - domain service remains business-truth/block-provider only

### `project.dashboard`
- carrier owner: `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
- full-contract owner: `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py`
- handler import path: `addons/smart_construction_core/handlers/project_dashboard_*`
- status: `platformized`
- notes:
  - minimal entry/runtime contract assembly is platform-owned
  - legacy full-contract `build()` path has been removed from domain service
  - `project.dashboard` full contract is now assembled by a platform-owned orchestrator

### `project.plan_bootstrap`
- carrier owner: `addons/smart_core/orchestration/project_plan_bootstrap_scene_orchestrator.py`
- handler import path: `addons/smart_construction_core/handlers/project_plan_bootstrap_*`
- status: `platformized`
- notes:
  - entry/runtime contract assembly is platform-owned
  - flow remains unchanged for existing `enter` and `block.fetch` intents

## Current Legacy Surface
- main product chain:
  - no remaining industry-local full-contract assembly on `execution / dashboard / plan_bootstrap`
- residual follow-up:
  - scene-specific pages outside the contract-driven main path still need separate frontend cleanup before broad architecture green can be declared

## Frontend Migration Status
- `frontend/apps/web/src/app/sceneMutationRuntime.ts`
  - status: `contract_only`
  - rule: execute path must use contract-provided `execute_intent`
  - removed: model-family implicit routing fallback
- `frontend/apps/web/src/layouts/AppShell.vue`
  - status: `contract/meta driven`
  - rule: shell presentation must come from route meta / contract context, not hardcoded business scene keys
- `frontend/apps/web/src/views/SceneView.vue`
  - status: `registry_only`
  - rule: scene resolution must come from the normalized scene registry only
  - removed: scene-ready runtime fallback reconstruction

## Legacy Exit Rules
- no new `*_scene_orchestrator.py` may be added under `addons/smart_construction_core/orchestration`
- scene handlers must import carriers from `odoo.addons.smart_core.orchestration.*`
- full scene/page/zones contract assembly must be owned by smart-core orchestrators, not domain services
- frontend mutation execution must fail closed when `execute_intent` is absent
- frontend main path must not branch on business-family models to decide execution intent
- any new business slice must start from platform-owned orchestration ownership and pass re-audit before implementation

## Reopen Slice Readiness
- status: `READY_FOR_SLICE`
- reason:
  - orchestration ownership for the main product chain is now correct on the core dashboard/plan/execution path
  - dashboard full-contract assembly no longer lives in domain service
  - frontend main path is contract-driven and zero raw business-semantic tokens remain outside the explicit baseline constant file
  - final slice readiness audit returns `READY_FOR_SLICE`

## Required Guards
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`
- `make verify.product.native_alignment_guard`
- `make verify.frontend.zero_business_semantics`
- `make verify.architecture.final_slice_readiness_audit`

## Next Recommended Step
- reopen the next business slice only from the current frozen baseline and keep `verify.architecture.final_slice_readiness_audit` plus `verify.product.v0_1_stability_baseline` green during the next round
