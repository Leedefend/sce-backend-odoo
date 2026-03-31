# ITER-2026-03-31-388 Report

## Summary

- Audited consistency between the accepted business-fact layer and the current custom frontend supplement surfaces.
- Conclusion:
  - `生命周期驾驶舱` -> materially aligned
  - `工作台` -> partially drifted from native business-fact anchor
  - `能力矩阵` -> route/target semantics still drift between backend scene facts and custom frontend route
- Because real consistency gaps were confirmed, this batch ends as `PASS_WITH_RISK` and should not auto-continue into implementation without opening a dedicated repair objective.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-388.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-388.md`
- `agent_ops/state/task_results/ITER-2026-03-31-388.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-388.yaml` -> PASS

## Architecture Declaration

- Layer Target: `Governance Audit`
- Affected Modules: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: validate that the accepted custom supplement surfaces still faithfully represent the industry business-fact layer, rather than drifting into standalone UI semantics

## Audit Basis

### 1. 工作台

#### Business-Fact Anchor

- native portal anchor:
  - `smart_construction_portal.action_sc_portal_dashboard`
- native fact builder:
  - `addons/smart_construction_core/services/portal_dashboard_service.py`
- scene contract expectation:
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - `portal.dashboard.summary`
  - `portal.dashboard.alerts`

#### Custom Frontend Surface

- `frontend/apps/web/src/views/HomeView.vue`
- `frontend/apps/web/src/views/MyWorkView.vue`

#### Consistency Result

`部分不一致`

Reason:

- `PortalDashboardService` still defines a fixed 5-entry business-fact dashboard registry.
- `portal.dashboard` scene layout still declares provider-based summary/alerts blocks.
- But `HomeView.vue` builds its visible entry set primarily from:
  - `session.scenes`
  - scene tiles
  - capability catalog/groups
- The custom workbench therefore remains product-usable, but it is no longer a tight frontend rendering of the native dashboard fact anchor.

### 2. 生命周期驾驶舱

#### Business-Fact Anchor

- native portal anchor:
  - `smart_construction_portal.action_sc_portal_lifecycle`
- lifecycle fact source:
  - `addons/smart_construction_core/services/lifecycle_capability_service.py`
- scene route / publication:
  - `portal.lifecycle`

#### Custom Frontend Surface

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`

#### Consistency Result

`基本一致`

Reason:

- the page loads scene entry data through `intentRequest`
- runtime blocks are hydrated through scene/runtime fetch hints
- current project context and lifecycle state are still sourced from backend facts rather than invented on the frontend

This surface is specialized, but it is still fact-driven enough for the current objective.

### 3. 能力矩阵

#### Business-Fact Anchor

- native portal anchor:
  - `smart_construction_portal.action_sc_portal_capability_matrix`
- fact contract:
  - `/api/contract/capability_matrix`
- scene contract:
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - scene code: `portal.capability_matrix`

#### Custom Frontend Surface

- `frontend/apps/web/src/views/CapabilityMatrixView.vue`
- `frontend/apps/web/src/api/capabilityMatrix.ts`
- SPA route:
  - `/s/portal.capability_matrix`

#### Consistency Result

`存在明确偏差`

Reason:

- the custom page correctly consumes the real capability-matrix contract
- but the backend scene layout for `portal.capability_matrix` still declares:
  - `target.route = '/s/project.management'`
- while the custom frontend actually exposes:
  - `/s/portal.capability_matrix`

So the page is fact-backed, but the publication target semantics are not yet fully aligned between backend scene facts and frontend route ownership.

## Main Conclusion

The consistency audit does **not** support a full “all aligned” conclusion.

Current state:

- `生命周期驾驶舱` -> acceptable alignment
- `工作台` -> usable but semantically broader than its original fact anchor
- `能力矩阵` -> fact-backed but scene target semantics still drift

## Risk Analysis

- Risk is real but localized.
- No forbidden paths were modified in this batch.
- The issue is not raw availability anymore; it is semantic drift between:
  - native fact anchor
  - scene publication metadata
  - custom frontend route ownership

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-388.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-388.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-388.json`

## Next Suggestion

- Open a dedicated low-risk consistency repair objective with two sub-lines:
  - align `portal.capability_matrix` scene publication target with the SPA-owned route
  - decide whether `工作台` should be explicitly reclassified as a product-level orchestration surface instead of pretending to still be a direct rendering of `PortalDashboardService`
