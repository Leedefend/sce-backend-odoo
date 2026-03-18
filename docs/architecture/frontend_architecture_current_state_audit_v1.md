# Frontend Architecture Current State Audit v1

## 1. Audit Scope

- Scope focuses on `frontend/apps/web/src` current implementation status.
- This iteration is **audit-only**: no runtime refactor, no feature expansion.
- Core files reviewed:
  - `frontend/apps/web/src/layouts/AppShell.vue`
  - `frontend/apps/web/src/views/ActionView.vue`
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/views/RecordView.vue`
  - `frontend/apps/web/src/views/SceneView.vue`
  - `frontend/apps/web/src/app/contracts/*`
  - `frontend/apps/web/src/app/runtime/*`
  - `frontend/apps/web/src/app/resolvers/*`

## 2. Target Baseline (Six Layers)

- Shell Layer
- Routing & Navigation Layer
- Contract Consumption Layer
- Runtime Execution Layer
- Page Assembly Layer
- Render Component Layer

Expected principle: frontend consumes backend contract/runtime artifacts, avoids business semantic inference in page layer.

## 3. Directory-to-Layer Mapping (Current)

| Path | Current Responsibility | Target Layer | Assessment |
| --- | --- | --- | --- |
| `frontend/apps/web/src/layouts/AppShell.vue` | app shell + navigation + HUD + extra business heuristics | Shell | Partial fit, still mixed |
| `frontend/apps/web/src/router` | router config and route entry | Routing | Exists |
| `frontend/apps/web/src/app/contracts` | ActionView contract normalization family | Contract Consumption | Good start, narrow coverage |
| `frontend/apps/web/src/app/runtime` | ActionView runtime extraction modules | Runtime Execution | Strong extraction, fragmented |
| `frontend/apps/web/src/app/resolvers` | action/scene registry resolution | Routing + Contract bridge | Mixed |
| `frontend/apps/web/src/views/*.vue` | page template + orchestration + runtime glue | Should be Shell+Assembly consumer | Still heavy |
| `frontend/apps/web/src/pages` | reusable page components, some runtime-heavy pages | Render (target) | Mixed purity |
| `frontend/apps/web/src/components` | shared components | Render | Mostly render, not fully pure |
| `frontend/apps/web/src/app/assemblers` | N/A | Page Assembly | **Missing** |
| `frontend/apps/web/src/app/routing` | N/A | Routing | **Missing (uses `src/router` + scattered helpers)** |
| `frontend/apps/web/src/app/shell` | N/A | Shell modules | **Missing** |

Evidence:
- Missing layer dirs confirmed by filesystem check.
- Present dirs: `app/contracts` (5 files), `app/runtime` (56 files), `app/resolvers` (6 files).

## 4. Six-Layer Status Assessment

### 4.1 Shell Layer

- `AppShell.vue` has valid shell responsibilities (sidebar/topbar/menu tree/router host/HUD host): `frontend/apps/web/src/layouts/AppShell.vue:8`, `frontend/apps/web/src/layouts/AppShell.vue:54`, `frontend/apps/web/src/layouts/AppShell.vue:104`, `frontend/apps/web/src/layouts/AppShell.vue:108`.
- It still contains business-oriented heuristics and diagnostics logic (delivery role label mapping / title inference / suggested-action export):
  - `frontend/apps/web/src/layouts/AppShell.vue:296`
  - `frontend/apps/web/src/layouts/AppShell.vue:309`
  - `frontend/apps/web/src/layouts/AppShell.vue:322`
  - `frontend/apps/web/src/layouts/AppShell.vue:515`

Conclusion: Shell exists but is not fully boundary-clean.

### 4.2 Routing & Navigation Layer

- Routing core exists under `frontend/apps/web/src/router`.
- Route logic still partially embedded in pages (`SceneView` route replacement and target resolution):
  - `frontend/apps/web/src/views/SceneView.vue:321`
  - `frontend/apps/web/src/views/SceneView.vue:400`
  - `frontend/apps/web/src/views/SceneView.vue:403`

Conclusion: Layer exists, but ownership is split between router and large views.

### 4.3 Contract Consumption Layer

- Dedicated contract modules exist (`actionViewStrictContract`, `actionViewSurfaceContract`, `actionViewProjectionContract`, `actionViewAdvancedContract`, sanitizer).
- Strict mode source-of-truth uses backend runtime policy/tier (no hardcoded core list): `frontend/apps/web/src/app/contractStrictMode.ts:30`.
- Current gap: contract layer is ActionView-centric, not generalized to all core views.

Conclusion: Contract layer is formed for pilot area, not platform-wide.

### 4.4 Runtime Execution Layer

- Significant extraction completed in `app/runtime` (56 files), especially ActionView family.
- ActionView imports many runtime modules: `frontend/apps/web/src/views/ActionView.vue:422` to `frontend/apps/web/src/views/ActionView.vue:743`.
- Runtime fragmentation risk: many micro-modules with strong page glue still kept in `ActionView` state host.

Conclusion: Runtime extraction is real, but current form is highly granular and still page-coupled.

### 4.5 Page Assembly Layer

- No dedicated assembler directory/module (`app/assemblers` missing).
- Page VM still assembled directly in `ActionView/HomeView/RecordView` through dense computed/ref/function sets.

Conclusion: This is the biggest structural gap.

### 4.6 Render Component Layer

- Reusable render components exist (`pages`, `components`).
- Purity is mixed: some page components remain runtime-heavy (e.g. `ContractFormPage` imports APIs directly).

Conclusion: Render layer partially exists; pure render boundary not consistently enforced.

## 5. AppShell Assessment

### 5.1 What fits AppShell

- Layout host, menu tree, topbar, breadcrumb, router host, status fallback panels are aligned with shell purpose.

### 5.2 What crosses layer

- Role/identity delivery heuristics inside shell (`normalizeDeliveryText`, `resolveDeliveryRoleLabel`).
- Business-ish title inference and trace export handling inside shell.

### 5.3 AppShell verdict

- Current stage: **usable shell with boundary leakage**.
- Recommended (next iteration, not in this audit): split shell-specific composables:
  - `useShellMenuTree`
  - `useShellBreadcrumb`
  - `useShellHudModel`
  - `useShellRoleSurface`

## 6. ActionView Assessment

### 6.1 Scale and density

- File size: `4020` lines (`frontend/apps/web/src/views/ActionView.vue`).
- Internal density sample: `computed=33`, `ref=32`, `functions=100`.

### 6.2 A/B/C/D status

| Category | Status | Evidence |
| --- | --- | --- |
| A. Already moved out | Yes | strict bundle and contracts imported (`ActionView.vue:749`, `ActionView.vue:759`, `ActionView.vue:768`) |
| B. Half moved | Yes | runtime modules imported, but view still hosts central state and orchestration (`ActionView.vue:803`, `ActionView.vue:843`) |
| C. Not moved | Yes | large `load()` orchestration remains in view (`ActionView.vue:2856`) |
| D. Should not remain in view | Yes | action/batch/refresh route orchestration still directly in page (`ActionView.vue:2678`, `ActionView.vue:3412`) |

### 6.3 ActionView verdict

- Current stage: **super component in transition** (not yet shell-grade page).
- Migration progressed, but state ownership and assembly ownership still concentrated in the page file.

## 7. RecordView / SceneView / HomeView Snapshot

### 7.1 RecordView

- Combines contract loading, data read/write flow, marker validation, view field projection in-page.
- Evidence: `frontend/apps/web/src/views/RecordView.vue:491` onward (`load()` full pipeline).
- Stage: **runtime-heavy page**.

### 7.2 SceneView

- Includes scene fallback reconstruction from `sceneReadyContractV1` and route-target execution in-page.
- Evidence: `frontend/apps/web/src/views/SceneView.vue:280`, `frontend/apps/web/src/views/SceneView.vue:321`.
- Stage: **route+orchestration mixed page**.

### 7.3 HomeView

- Contains keyword-based action labeling and multiple fallback text branches.
- Evidence: `frontend/apps/web/src/views/HomeView.vue:1046`, `frontend/apps/web/src/views/HomeView.vue:1228`.
- Stage: **business-semantics mixed page**.

### 7.4 Priority order for next wave

1. `ActionView`
2. `HomeView`
3. `RecordView`
4. `SceneView`

## 8. Contract Layer Evaluation

### 8.1 Positive

- Strict consumption entry exists (`useActionViewStrictContractBundle`).
- Backend-driven strict mode policy exists (`contractStrictMode.ts`).

### 8.2 Gaps

- Contract layer still contains UI fallback labels/hints in resolvers (`actionViewSurfaceContract.ts:150` onward).
- Layer coverage not generalized beyond ActionView.

Verdict: **formed but scoped and partially mixed with UI fallback policy**.

## 9. Runtime Layer Evaluation

### 9.1 Positive

- Real extraction happened (56 runtime files).
- Group/batch/load subflows are modularized.

### 9.2 Risk

- Fragmentation: too many narrowly-scoped modules may increase glue complexity.
- Some runtime modules still carry text fallback behavior (`actionViewBatchHintResolverRuntime.ts:51`).

Verdict: **effective extraction, but partially mechanical/over-sliced**.

## 10. Page Assembly Gap Assessment

- `app/assemblers` is absent; no canonical page VM aggregator.
- Views still feed templates directly with numerous refs/computed and branch logic.

Verdict: **Page Assembly layer is missing** and is the primary bottleneck for full architecture closure.

## 11. Render Layer Assessment

- Mixed maturity:
  - Good reusable render surfaces: `ListPage`, `KanbanPage`, shared components.
  - Non-pure pages/components exist with direct API access:
    - `frontend/apps/web/src/pages/ContractFormPage.vue:300`
    - `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue:48`

Verdict: render layer is **partially mature but not uniformly pure**.

## 12. Architecture Violation Summary

- Detailed inventory: `docs/architecture/frontend_architecture_violation_inventory_v1.md`.
- Key blockers:
  - Missing page assembly layer.
  - Heavy page-level orchestration in `ActionView`.
  - Residual page-level business heuristics (`HomeView`).

## 13. Reusable Asset Summary

- Detailed inventory: `docs/architecture/frontend_architecture_asset_inventory_v1.md`.
- Current reusable base is sufficient to start next wave without redesign from scratch.

## 14. Final Conclusion (Input for Next Iteration)

Current frontend state is:

- **not old flat page stack anymore**,
- **not yet six-layer closed architecture**,
- best described as **runtime-splitting transition stage**.

Primary bottleneck is **missing Page Assembly layer** (page VM ownership). Next iteration should prioritize:

1. Build `ActionView` page-assembly model (`useActionPageModel` equivalent).
2. Move remaining central state/process ownership out of `ActionView.vue`.
3. Apply same pattern to `HomeView` after ActionView closure.

Do-not-touch first in next wave:

- broad shell redesign,
- router rewrite,
- global component-library refactor.

