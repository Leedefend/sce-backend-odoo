# Phase 16-C: Five-Layer Reality Audit

## Objective
- audit the repository against the intended five-layer architecture before any further product expansion
- determine whether the next iteration should focus on business growth or architecture consolidation

## Audit Baseline
- audit date: `2026-03-22`
- branch: `codex/next-round`
- head: `e3a598f`

## Executive Conclusion
- overall status: `amber`
- conclusion:
  - the repository is no longer on the wrong path
  - but the five-layer implementation is not yet fully platformized
  - the next stage should prioritize orchestration consolidation, not new business slice expansion

## Layer-by-Layer Assessment

### 1. Business Truth Layer
- status: `strong`
- evidence:
  - existing business carriers already cover the near-term product facts:
    - `project.project`
    - `project.task`
    - `payment.request`
    - `account.move`
    - `project.budget`
    - `project.cost.ledger`
    - `construction.contract`
- assessment:
  - lack of business facts is not the bottleneck
  - future expansion should reuse these carriers instead of creating new project-scoped business families

### 2. Native Expression Layer
- status: `usable`
- assessment:
  - Odoo-native carriers and views already exist
  - however, product delivery still lacks a uniform native handoff strategy for the next chain

### 3. Native Parse Layer
- status: `available`
- evidence:
  - `addons/smart_scene/core/scene_engine.py`
  - `addons/smart_core/core/scene_runtime_orchestrator.py`
- assessment:
  - core parse/orchestration infrastructure exists
  - but industry-side delivery still partially assembles orchestration behavior inside domain-side modules

### 4. Contract Governance Layer
- status: `strong`
- evidence:
  - `scripts/verify/product_native_alignment_guard.py`
  - `scripts/verify/five_layer_workspace_audit.py`
- verification:
  - `make verify.product.native_alignment_guard` => `PASS`
  - `make verify.architecture.five_layer_workspace_audit` => `PASS`
- assessment:
  - governance is strong enough to prevent the previous shadow direction from re-entering the codebase

### 5. Scene Orchestration Layer
- status: `partially aligned`
- evidence:
  - explicit carrier adapters now exist for:
    - `project.dashboard`
    - `project.plan_bootstrap`
    - `project.execution`
- assessment:
  - responsibility separation is improved
  - but module ownership is still mixed:
    - orchestration carriers are still stored under `smart_construction_core`
    - some orchestration-related assembly remains coupled to industry services

### 6. Frontend Layer
- status: `mostly aligned with residual exceptions`
- assessment:
  - the main project dashboard path now consumes generic scene contract fields
  - residual scene/model-specific branching still exists in a few runtime points

## Positive Corrections Already Landed
- shadow `project.payment.*` direction has been retired
- `execution`, `dashboard`, and `plan_bootstrap` now use explicit orchestration carriers
- frontend project dashboard path no longer branches on concrete `project.*.enter`
- double-guard governance is in place and passing

## Residual Risks

### Risk 1: platform vs industry split is still incomplete
- evidence:
  - `addons/smart_construction_core/orchestration/project_dashboard_scene_orchestrator.py`
  - `addons/smart_construction_core/orchestration/project_plan_bootstrap_scene_orchestrator.py`
  - `addons/smart_construction_core/orchestration/project_execution_scene_orchestrator.py`
- interpretation:
  - orchestration responsibility is separated from pure domain service
  - but not yet fully moved into a reusable platform-side scene orchestration path

### Risk 2: dashboard still shows dual orchestration styles
- evidence:
  - `addons/smart_construction_core/services/project_dashboard_service.py`
- interpretation:
  - the service now provides truth-facing block output
  - but also still contains a `build()` path that assembles a larger scene/page/zones contract
  - this means the repository currently carries both:
    - minimal product carrier style
    - full scene-contract assembly style
- risk:
  - future work may split across two orchestration styles and recreate architectural drift

### Risk 3: frontend still contains small hardcoded scene/model decisions
- evidence:
  - `frontend/apps/web/src/layouts/AppShell.vue`
  - `frontend/apps/web/src/app/sceneMutationRuntime.ts`
- interpretation:
  - `projects.intake` still has shell-level special presentation
  - mutation runtime still routes by concrete model family
- risk:
  - these are not catastrophic now
  - but they remain against the long-term rule that frontend should consume orchestration output rather than product semantics

## Decision
- do not start a new v0.2 business chain yet
- do not re-open `payment / contract / cost` product slicing until orchestration ownership is clearer
- treat the next stage as architecture consolidation

## Recommended Next Iteration Direction
1. move scene orchestration ownership closer to `smart_scene` platform mechanisms
2. converge the repository onto one orchestration delivery style
3. remove residual frontend scene/model hardcoding
4. only after those are stable, reopen second-chain product expansion

## Suggested Batch Order
1. `Phase 16-D`
   - scene orchestration platformization
   - decide standard carrier/provider pattern
2. `Phase 16-E`
   - frontend residual hardcoding cleanup
   - generic mutation routing / shell copy sourcing
3. `Phase 16-F`
   - re-audit five-layer compliance
   - only then decide the next business chain

## Final Assessment
- the repository is no longer architecture-blocked
- but it is not yet architecture-frozen
- the correct next move is consolidation, not expansion
