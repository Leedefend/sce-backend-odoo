# Five-Layer Architecture Full Audit - Phase 16-B

## Audit Goal
- Verify whether the current repository and workspace are advancing along the required five-layer path:
  - Business Truth
  - Native Expression
  - Native Parse
  - Contract Governance
  - Scene Orchestration
- Confirm that future business expansion can be built by reusing existing business truth assets instead of adding new project-scoped business implementations.

## Executive Conclusion
- Overall result: `blocked`
- Positive baseline: the repository already contains enough business-truth carriers for the next stage.
- Primary problem: product delivery is still mixing `business truth`, `scene orchestration`, and `frontend consumption` responsibilities.

## What Is Already Strong Enough

### Business Truth Layer
- Existing carriers are not the bottleneck:
  - `project.project`
  - `project.task`
  - `payment.request`
  - `construction.contract`
  - `project.budget`
  - `project.cost.ledger`
  - `account.move`
  - `account.move.line`
- Conclusion:
  - future work should reuse these facts
  - we do not need more project-scoped business models or shadow lifecycles

### Contract / Orchestration Infrastructure
- Existing platform material is already present:
  - `smart_core` page orchestration contracts
  - `semantic_page` / `native_view` contract chain
  - `smart_scene` scene engine hooks
- Conclusion:
  - the core task is consolidation onto this path, not more one-off product runtime services

## Findings

### Finding 1: Scene orchestration is still implemented inside domain-side product services
- Evidence:
  - `addons/smart_construction_core/services/project_dashboard_service.py`
  - `addons/smart_construction_core/services/project_plan_bootstrap_service.py`
  - `addons/smart_construction_core/services/project_execution_service.py`
  - `addons/smart_construction_core/services/project_payment_service.py` in current workspace draft
- Symptom:
  - these services directly build `title / blocks / suggested_action / runtime_fetch_hints`
  - they behave like scene-entry assemblers rather than business-truth services
- Layer impact:
  - Scene Orchestration responsibility is co-located in domain module implementation
- Required correction:
  - keep truth logic in business services
  - move scene assembly into explicit orchestration adapters or scene-layer providers

### Finding 2: Frontend still branches on concrete project scene intents
- Evidence:
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- Symptom:
  - explicit checks on `project.plan_bootstrap.enter`
  - explicit checks on `project.execution.enter`
  - explicit checks on `project.payment.enter`
  - block-key-specific rendering for custom runtime blocks
- Layer impact:
  - frontend is deciding product structure from scene intent names
- Why this is a problem:
  - violates the rule that frontend consumes orchestration contract, not concrete scene-name semantics
- Required correction:
  - frontend should render generic orchestration contract fields
  - scene-specific wording should come from backend contract, not hardcoded branch logic

### Finding 3: Shadow business scene family is being introduced for payment
- Evidence:
  - `addons/smart_construction_core/handlers/project_payment_enter.py`
  - `addons/smart_construction_core/handlers/project_payment_block_fetch.py`
  - `addons/smart_construction_core/handlers/project_payment_ensure_single.py`
  - `addons/smart_construction_core/services/project_payment_*`
  - `scripts/verify/product_project_payment_flow_smoke.py`
- Symptom:
  - `project.payment.*` creates a project-scoped finance scene family
- Layer impact:
  - business facts are no longer merely orchestrated; they are being re-expressed as a new project product flow
- Required correction:
  - freeze and remove this direction
  - replace with native finance scene handoff

### Finding 4: Verify assets are starting to freeze the wrong surface
- Evidence:
  - `scripts/verify/product_project_payment_flow_smoke.py`
  - `Makefile` target `verify.product.project_payment_flow_smoke`
- Symptom:
  - verify chain validates a shadow path instead of native handoff
- Layer impact:
  - governance starts protecting the wrong architecture
- Required correction:
  - replace shadow-flow smoke with native-handoff smoke after redesign approval

## Architecture Reading of the Current State

### Business Truth Layer
- Status: `usable`
- Issue:
  - not being treated as the primary source for the next expansion strategy

### Native Expression Layer
- Status: `partially reusable`
- Issue:
  - product expansion is not consistently anchoring to existing native scenes and forms

### Native Parse Layer
- Status: `available but underused`
- Issue:
  - product features are still arriving through bespoke runtime blocks instead of standardized parse -> governance -> orchestration chain

### Contract Governance Layer
- Status: `strong at platform level, weak at project-product level`
- Issue:
  - project-specific runtime contracts are proliferating outside the main orchestration contract family

### Scene Orchestration Layer
- Status: `strategically correct, structurally mixed`
- Issue:
  - orchestration exists, but much of it is implemented inside domain addon services instead of a clearly bounded orchestration layer

## Required Correction Order
1. Freeze all new `project.payment.* / project.contract.* / project.cost.*` scene families.
2. Treat existing business models as the only truth carriers for business expansion.
3. Move product entry assembly toward explicit scene orchestration adapters.
4. Refactor frontend product pages to consume generic orchestration contract, not scene-name branches.
5. Replace feature smokes that validate shadow flows with smokes that validate native handoff and contract consumption.

## Decision
- The repository does not need more business facts first.
- The repository needs a cleaner Scene Orchestration Layer and stricter frontend contract consumption.
- From this point on, architecture progress should be measured by:
  - fewer shadow intents
  - fewer frontend scene branches
  - more native-scene handoff
  - more orchestration-contract reuse
