# Phase 16-D / Next Batch: Orchestration Platformization

## Objective
- complete platformization for the remaining main product chain scenes
- unify orchestration style for `dashboard`, `plan_bootstrap`, and `execution`
- remove frontend legacy mutation routing fallback
- rerun architecture audit before reopening any business expansion

## Delivered

### 1. Dashboard Orchestration Platformization
- moved `project.dashboard` scene carrier ownership to:
  - `addons/smart_core/orchestration/project_dashboard_scene_orchestrator.py`
- updated `project.dashboard.enter` and `project.dashboard.block.fetch` handlers to import the smart-core carrier
- removed the old industry-local dashboard carrier file
- public contract stays unchanged

### 2. Plan Bootstrap Orchestration Platformization
- moved `project.plan_bootstrap` scene carrier ownership to:
  - `addons/smart_core/orchestration/project_plan_bootstrap_scene_orchestrator.py`
- updated `project.plan_bootstrap.enter` and `project.plan_bootstrap.block.fetch` handlers to import the smart-core carrier
- removed the old industry-local plan carrier file
- existing flow remains unchanged

### 3. Unified Frontend Mutation Routing
- `frontend/apps/web/src/app/sceneMutationRuntime.ts` now executes mutations only through contract-provided `execute_intent`
- removed model-family implicit fallback routing
- mutation contract now fails closed when `execute_intent` is missing

### 4. Frontend Main-Path Residual Semantics
- re-scanned the main path for business-key hardcoding
- this batch keeps the fix scope limited to contract-driven main path
- no expansion into scene-specific legacy pages such as intake-only pages

### 5. Migration Status and Re-Audit
- added `docs/ops/orchestration_migration_status_v1.md`
- rerun architecture ownership/hardcoding/readiness audit after migration

## Re-Audit Conclusion
- status: `amber`
- judgement:
  - `execution / dashboard / plan_bootstrap` minimal carriers are now platform-owned
  - frontend contract execution path is now aligned with contract-driven routing
  - remaining blocker for reopening new slices is the legacy full-contract builder in `project_dashboard_service.py`
- decision:
  - do not reopen new business slice yet
  - continue one more convergence round on legacy dashboard full-contract ownership

## Verification Target
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`
- `make verify.product.native_alignment_guard`
- `make verify.product.project_dashboard_entry_contract_guard DB=sc_demo`
- `make verify.product.project_dashboard_block_contract_guard DB=sc_demo`
- `make verify.product.project_plan_entry_contract_guard DB=sc_demo`
- `make verify.product.project_plan_block_contract_guard DB=sc_demo`
- `make verify.product.project_execution_entry_contract_guard DB=sc_demo`
- `make verify.product.project_execution_block_contract_guard DB=sc_demo`
- `make verify.product.project_execution_state_smoke DB=sc_demo`
- `make verify.frontend_api DB=sc_demo`
