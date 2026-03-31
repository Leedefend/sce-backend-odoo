# ITER-2026-03-31-392 Report

## Summary

- Audited whether the current custom frontend surfaces still align with the native business-fact layer (`model / view / action`).
- Audited whether those custom surfaces can actually complete business handling flows instead of only rendering read-only or navigation-only shells.
- Classified the current surfaces into explicit transactability categories.

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-392.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-392.md`
- `agent_ops/state/task_results/ITER-2026-03-31-392.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-392.yaml` -> PASS

## Audit Scope

This audit focused on the active custom frontend surfaces that currently stand in
for the abandoned native portal frontend:

- `工作台`
- `我的工作`
- `生命周期驾驶舱`
- `能力矩阵`

Finance-governed high-risk claims were intentionally excluded from the positive
transactability set. In particular, payment / settlement / treasury handling was
not used to justify a PASS classification.

## Surface Classification

### 1. `工作台`

Classification: `navigation_only`

#### Fact Basis

- Native fact anchor still exists:
  - `addons/smart_construction_core/controllers/portal_dashboard_controller.py`
  - `addons/smart_construction_core/services/portal_dashboard_service.py`
- Scene layer still publishes `portal.dashboard` as a dashboard-oriented surface:
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
- Current custom page:
  - `frontend/apps/web/src/views/HomeView.vue`

#### Evidence

- `HomeView.vue` is built around orchestration/session state:
  - `homeOrchestrationContract`
  - `session.scenes`
  - `session.capabilityGroups`
- It acts as a landing/orchestration surface and does not expose direct business
  mutation handling.

#### Decision

`工作台` is aligned as a product landing/orchestration surface, but it does not
itself complete business handling. Its role is entry routing and prioritization.

### 2. `我的工作`

Classification: `aligned_and_transactable`

#### Fact Basis

- Frontend:
  - `frontend/apps/web/src/views/MyWorkView.vue`
  - `frontend/apps/web/src/api/myWork.ts`
- Backend:
  - `addons/smart_construction_core/handlers/my_work_complete.py`

#### Evidence

- `MyWorkView.vue` supports:
  - single item open / routing
  - batch selection
  - batch completion
  - retry of failed items
- `api/myWork.ts` calls real intents:
  - `my.work.summary`
  - `my.work.complete`
  - `my.work.complete_batch`
- `my_work_complete.py` implements actual completion behavior for `mail.activity`
  items, including batch execution, idempotency, failure grouping, and replay.

#### Decision

`我的工作` is not just a dashboard shell. For the todo/mail-activity subset, it
already provides true business handling capability and is materially aligned
with the underlying business fact chain.

### 3. `生命周期驾驶舱`

Classification: `aligned_and_transactable`

#### Fact Basis

- Frontend:
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue`
- Scene/runtime contract chain:
  - runtime block fetch via `intentRequest`
  - scene entry loading via `*.enter` intents

#### Evidence

- `ProjectManagementDashboardView.vue` performs real runtime loading through
  intent-based scene entry and block fetches.
- It can execute actual scene/business actions through `runAction(action)`.
- It includes direct handling flows such as:
  - scene transitions / action execution
  - project context switching
  - cost-entry submission via `submitCostEntry()`
- It reloads the scene after action execution, which indicates a real handling
  loop instead of a static visualization-only page.

#### Boundary Note

- `submitPaymentEntry()` exists in the same page, but payment belongs to the
  finance-governed high-risk domain and was excluded from the positive claim
  set for this audit.

#### Decision

For the non-finance subset, `生命周期驾驶舱` is materially aligned with the
business fact layer and supports actual business handling instead of only
viewing or navigating.

### 4. `能力矩阵`

Classification: `aligned_but_readonly`

#### Fact Basis

- Frontend:
  - `frontend/apps/web/src/views/CapabilityMatrixView.vue`
  - `frontend/apps/web/src/api/capabilityMatrix.ts`
- Backend:
  - `/api/contract/capability_matrix`
  - `addons/smart_construction_core/services/capability_matrix_service.py`

#### Evidence

- The page consumes the real backend contract instead of inventing local data.
- It renders real grouped capability items and normalizes native anchors into
  SPA routes.
- It does not execute mutations or complete business records.
- Its action model is governance/readability/navigation:
  - inspect capability availability
  - open an allowed route

#### Decision

`能力矩阵` is aligned with the fact layer, but it is intentionally read-only.
It is not a business-handling surface.

## Main Conclusion

The current custom frontend surfaces are not all the same type:

- `工作台` = navigation/orchestration surface
- `我的工作` = true business-handling surface
- `生命周期驾驶舱` = true business-handling surface for the non-finance subset
- `能力矩阵` = fact-aligned read-only governance surface

Therefore the correct statement is not:

- "all custom frontend surfaces can办理业务"

The correct statement is:

- some custom surfaces already support real business handling
- some are intentionally read-only or navigation-oriented
- the current system is mixed by design, and this should be described explicitly
  rather than flattened into a single transactability claim

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No implementation files were modified.
- The only caution is semantic: future product messaging should stop implying
  that every custom page is equally transactable.

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-392.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-392.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-392.json`

## Next Suggestion

- If a next batch is needed, it should target only the surfaces that still need
  stronger办理闭环 instead of treating all custom frontend pages the same.
- The most natural follow-up is to decide whether `工作台` should remain a pure
  orchestration surface or gain a minimal actionable handling slice.
