# Phase 16-D: Dashboard Full-Contract Platformization

## Objective
- remove the remaining dashboard full-contract ownership from domain service
- move `project.dashboard` scene/page/zones assembly into `smart_core/orchestration`
- rerun architecture audit after the migration and re-evaluate reopen-slice readiness

## Delivered

### 1. Platform-Owned Dashboard Full Contract
- added:
  - `addons/smart_core/orchestration/project_dashboard_contract_orchestrator.py`
- moved ownership of:
  - scene content provider loading
  - dashboard zone assembly
  - scene/page/zones contract build
  - route context assembly
  - compat `dashboard_contract_v1` projection
- `addons/smart_construction_core/handlers/project_dashboard.py` now depends on the smart-core orchestrator instead of domain service contract assembly

### 2. Domain Service Cleanup
- removed dashboard full-contract `build()` path from:
  - `addons/smart_construction_core/services/project_dashboard_service.py`
- retained only:
  - project resolution
  - business-truth projection
  - runtime block provider responsibilities

### 3. Guard and Contract Baseline Refresh
- tightened `orchestration_platform_guard` so dashboard full-contract assembly is forbidden inside domain service
- refreshed dashboard contract guards to follow current reality:
  - builder count no longer hardcoded to exactly 7
  - `action_list` runtime builder is treated as valid
  - capability mapping baseline now points to `project.dashboard.enter`
  - metric semantics guard matches the current contract-driven main path instead of an outdated rich-page assumption

## Re-Audit Conclusion
- status: `ready_for_decision`
- judgement:
  - `execution / dashboard / plan_bootstrap` orchestration ownership is now platform-owned on both minimal carriers and dashboard full contract
  - `orchestration_platform_guard`, `five_layer_workspace_audit`, and `native_alignment_guard` all pass
  - architecture no longer blocks the decision to reopen a new business slice
- caution:
  - some scene-specific frontend pages outside the contract-driven main path still deserve a separate cleanup round

## Verification
- `make verify.project.dashboard.contract`
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`
- `make verify.product.native_alignment_guard`
- `make restart`
- `make verify.product.project_dashboard_entry_contract_guard DB=sc_demo`
- `make verify.product.project_dashboard_block_contract_guard DB=sc_demo`
- `make verify.product.project_execution_entry_contract_guard DB=sc_demo`
- `make verify.frontend_api DB=sc_demo`
