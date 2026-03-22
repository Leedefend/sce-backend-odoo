# Phase 16-D: Orchestration Platformization

## Objective
- move scene orchestration out of business-module ownership and into a platform-owned path
- prove the direction with an `execution` pilot
- reduce residual frontend business semantics
- add a dedicated guard for orchestration platformization

## Delivered
- defined a platform-side orchestration carrier path under `addons/smart_core/orchestration`
- moved `project.execution` carrier ownership to `smart_core`
- marked remaining industry-local carriers as legacy mode
- reduced frontend hardcoded business semantics in shell and mutation runtime
- added executable orchestration platform guard

## Key Changes

### 1. Platform Orchestration Layer
- new platform carrier package:
  - `addons/smart_core/orchestration/__init__.py`
  - `addons/smart_core/orchestration/base_scene_entry_orchestrator.py`
  - `addons/smart_core/orchestration/project_execution_scene_orchestrator.py`
- result:
  - `execution` scene entry/runtime carrier is now platform-owned
  - industry module keeps business-truth services, not execution carrier assembly

### 2. Execution Pilot Extraction
- `project_execution_enter` and `project_execution_block_fetch` now import the carrier from `smart_core`
- old `addons/smart_construction_core/orchestration/project_execution_scene_orchestrator.py` is removed
- execution regression chain remains green

### 3. Unified Style / Old-Mode Marker
- remaining industry-local carriers now explicitly declare:
  - `LEGACY_ORCHESTRATION_MODE = "industry_local"`
- this applies to:
  - `project_dashboard`
  - `project_plan_bootstrap`
- meaning:
  - they are still tolerated
  - but they are no longer the target style for new work

### 4. Frontend De-business-semantics
- `AppShell.vue` no longer hardcodes `projects.intake` shell presentation
- `sceneMutationRuntime.ts` now prefers contract-provided `execute_intent`
- model-based execute routing is retained only as legacy fallback
- mutation parameter assembly is now driven more by schema/context than by explicit model branches

### 5. Platformization Guard
- added:
  - `scripts/verify/orchestration_platform_guard.py`
  - `make verify.architecture.orchestration_platform_guard`
- guard enforces:
  - platform execution carrier exists in `smart_core`
  - old execution carrier path under industry module is absent
  - remaining industry-local carriers are explicitly marked as legacy
  - frontend must not reintroduce the audited business-semantic branch patterns

## Verification
- `make verify.architecture.orchestration_platform_guard` => `PASS`
- `make verify.architecture.five_layer_workspace_audit` => `PASS`
- `make verify.product.native_alignment_guard` => `PASS`
- `make restart` => `PASS`
- `make verify.product.project_execution_entry_contract_guard DB=sc_demo` => `PASS`
- `make verify.product.project_execution_block_contract_guard DB=sc_demo` => `PASS`
- `make verify.product.project_execution_state_smoke DB=sc_demo` => `PASS`
- `make verify.frontend_api DB=sc_demo` => `PASS`

## Remaining Follow-up
- `dashboard` and `plan_bootstrap` orchestration ownership is still not fully platformized
- frontend mutation runtime still contains legacy fallback mapping and should eventually be replaced by contract-only routing
- the next correct step is residual cleanup and a narrower platform/provider convergence round, not business expansion
