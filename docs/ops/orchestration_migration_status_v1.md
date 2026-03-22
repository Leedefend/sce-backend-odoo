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
- handler import path: `addons/smart_construction_core/handlers/project_dashboard_*`
- status: `platformized`
- notes:
  - minimal entry/runtime contract assembly is platform-owned
  - legacy full-contract `build()` path still exists in domain service and is not the target style for new work

### `project.plan_bootstrap`
- carrier owner: `addons/smart_core/orchestration/project_plan_bootstrap_scene_orchestrator.py`
- handler import path: `addons/smart_construction_core/handlers/project_plan_bootstrap_*`
- status: `platformized`
- notes:
  - entry/runtime contract assembly is platform-owned
  - flow remains unchanged for existing `enter` and `block.fetch` intents

## Current Legacy Surface
- `addons/smart_construction_core/services/project_dashboard_service.py`
  - still contains `build()` for full `scene/page/zones` contract assembly
  - classification: `legacy tolerated`
  - exit rule: no new callers; future platform round should converge this path into smart-core-owned provider/orchestration style

## Frontend Migration Status
- `frontend/apps/web/src/app/sceneMutationRuntime.ts`
  - status: `contract_only`
  - rule: execute path must use contract-provided `execute_intent`
  - removed: model-family implicit routing fallback
- `frontend/apps/web/src/layouts/AppShell.vue`
  - status: `contract/meta driven`
  - rule: shell presentation must come from route meta / contract context, not hardcoded business scene keys

## Legacy Exit Rules
- no new `*_scene_orchestrator.py` may be added under `addons/smart_construction_core/orchestration`
- scene handlers must import carriers from `odoo.addons.smart_core.orchestration.*`
- frontend mutation execution must fail closed when `execute_intent` is absent
- frontend main path must not branch on business-family models to decide execution intent
- any remaining industry-local full-contract builder must be explicitly documented as legacy and scheduled for convergence before reopening new business slices

## Reopen Slice Readiness
- status: `not_ready`
- reason:
  - orchestration ownership for the main product chain is now mostly correct
  - but legacy full-contract assembly still exists in `project_dashboard_service.py`
  - frontend main path is cleaner, yet residual scene-specific pages outside the contract-driven main path still need separate treatment

## Required Guards
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`
- `make verify.product.native_alignment_guard`

## Next Recommended Step
- converge the remaining dashboard full-contract `build()` path into a platform-owned provider/orchestration pattern, then rerun five-layer audit before reopening any new business slice
