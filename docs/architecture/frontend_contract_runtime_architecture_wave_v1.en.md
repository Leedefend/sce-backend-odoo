# Frontend Contract Runtime Architecture Wave v1

Chinese version: `docs/architecture/frontend_contract_runtime_architecture_wave_v1.md`

## 1. Iteration Positioning

### 1.1 Target Type

This wave is an architecture-level refactor, not page-level patching or visual tuning.

### 1.2 Target State

Frontend evolves from a semi-interpretive page stack (page component + local contract reads + local semantic guessing + local runtime execution) to a strict contract runtime architecture (contract consumption + generic runtime + page assembly + pure rendering).

### 1.3 Core Objectives of This Wave

- Backend becomes the only business semantic source.
- Frontend no longer owns business semantic interpretation.
- Pages only consume contracts, assemble page VMs, and render.
- Core pages run in strict contract mode.
- Stable interfaces are prepared for multi-frontend reuse.

## 2. Architecture Principles

### 2.1 Single Semantic Source

Backend is the only business semantic source. Frontend must not infer semantics by keywords, field combinations, default copy, or ad-hoc rules.

### 2.2 Contract-First

Frontend pages consume runtime contract artifacts only: `scene_ready`, `page_contract`, `projection`, `action_surface`, `semantic_cells`, `runtime_policy`.

### 2.3 Runtime/Rendering Separation

Runtime executes; rendering displays. Render components must not call business APIs directly and must not interpret raw contracts.

### 2.4 Strict-Mode Priority

Strict contract mode is decided by:

1. `runtime_policy.strict_contract_mode=true`
2. `scene_tier=core`

Frontend must not maintain a local core-scene allowlist as source of truth.

### 2.5 Fallback Boundaries

Allowed fallback is UI-only: `loading`, `empty`, `error`, style defaults, neutral copy defaults.

Forbidden fallback includes: page-type guessing, action-group guessing, business summary aggregation guessing, business semantic status inference.

## 3. Runtime Consumption Convention

- Preferred runtime source: `scene_ready`
- Secondary source only when not yet materialized in `scene_ready`: `scene_contract`
- Frontend must follow declared source priority and must not merge semantic truth by heuristics.

## 4. Six-Layer Frontend Model

### 4.1 `Shell Layer`

Responsibilities: app shell, global layout, session container, global error boundary, topbar/sidebar/HUD host.

Input: `session/app.init`, global route state.

Output: shell layout capabilities, global context container.

Forbidden: business semantic interpretation, business action execution, page contract parsing.

### 4.2 `Routing & Navigation Layer`

Responsibilities: `scene/action/record` route resolution, query/context normalization, navigation intent dispatch.

Input: Vue Router, route params/query, menu/action metadata.

Output: normalized route context, normalized navigation target.

Forbidden: page semantic decisions, business UI structure generation.

### 4.3 `Contract Consumption Layer`

Responsibilities: parse and normalize `scene_ready`, `scene_contract`, `page_contract`, `projection`, `action_surface`, `semantic_cells`, `runtime_policy`.

Output: `resolvedSurface`, `resolvedProjection`, `resolvedActionSurface`, `resolvedViewModes`, `resolvedStrictPolicy`.

Forbidden: direct rendering, direct business action execution, semantic backfilling by heuristics.

### 4.4 `Runtime Execution Layer`

Responsibilities: list/form/group/mutation/batch/projection-refresh runtime execution.

Input: contract consumption outputs, route context, session context.

Output: runtime state, executable handlers, load/refresh results.

Forbidden: business semantic inference, business copy generation, page-structure decisions.

### 4.5 `Page Assembly Layer`

Responsibilities: assemble page VM from contract outputs + runtime state.

Standard outputs: `headerVM`, `filterVM`, `groupVM`, `actionVM`, `contentVM`, `strictAlertVM`, `hudVM`.

Forbidden: direct API calls, direct raw-contract interpretation, direct template logic coupling.

### 4.6 `Render Component Layer`

Responsibilities: pure rendering via `props + emits`.

Input: Page VM, Section VM, Block VM.

Output: visible UI.

Forbidden: direct raw-contract consumption, direct business API calls, cross-layer runtime mutation.

## 5. Inter-Layer Dependency Rules

Dependency direction must remain one-way:

```text
Shell Layer
  -> Routing & Navigation Layer
  -> Contract Consumption Layer
  -> Runtime Execution Layer
  -> Page Assembly Layer
  -> Render Component Layer
```

Allowed dependencies:

- `views/shell` -> `assemblers`
- `assemblers` -> `contracts` and `runtime`
- `runtime` -> `contracts` and `routing`
- `render components` -> `props/emits` and UI primitives only

Forbidden dependencies:

- `Render Component Layer -> business API`
- `Render Component Layer -> raw contract`
- `Shell Layer -> business runtime`
- `Page Assembly Layer -> backend adapter`
- `Runtime Execution Layer -> heuristic semantic resolver`

## 6. Runtime Data Flow

All core pages follow this flow:

```text
Route Context
+ Session Context
+ Scene Ready / Page / Projection / Action Surface Contract
-> Contract Consumption Layer
-> Runtime Execution Layer
-> Page Assembly Layer
-> Render Component Layer
```

Contract-missing fallback may preserve shell usability, but must not fabricate business labels, grouping, summaries, or semantic statuses.

## 7. Target Directory Layout

```text
frontend/apps/web/src/
  app/
    shell/
    routing/
    contracts/
    runtime/
    assemblers/
  views/
    ActionViewShell.vue
    HomeViewShell.vue
    RecordViewShell.vue
    SceneViewShell.vue
  sections/
  pages/
  fields/
  blocks/
```

Directory constraints:

- `app/contracts/`: contract consumption and normalization only
- `app/runtime/`: runtime execution only
- `app/assemblers/`: page VM assembly only
- `views/`: page shell components only
- `sections/pages/fields/blocks/`: pure rendering only

## 8. `ActionView` Decomposition Targets

### 8.1 Decomposition Principle

`ActionView` is no longer a super-controller and is reduced to a page shell.

### 8.2 Target Modules

- `useActionViewContract.ts`: strict mode + surface/projection/action-surface/advanced-view contract consumption.
- `useActionViewListRuntime.ts`: loading/search/sort/group/window sync + route preset sync.
- `useActionViewActionRuntime.ts`: header/contract actions, mutation execution, refresh policy, record navigation.
- `useActionViewBatchRuntime.ts`: batch actions, failed preview, retry/idempotency.
- `useActionPageModel.ts`: unified page VM assembly from contract + runtime.
- `ActionViewShell.vue`: section assembly and rendering only.

## 9. Wave Execution Plan

### Wave A: Skeleton and Boundaries

- Create `contracts/runtime/assemblers` layout and boundary rules.
- Introduce `ActionViewShell + composable` skeleton.
- Add boundary guards and ban new heuristics.

### Wave B: Action Main-Chain Migration

- Move contract consumption out of `ActionView.vue`.
- Move list/action/batch runtime out of `ActionView.vue`.
- Move strict-mode branching down to contract/runtime layers.
- Remove keyword/action-group/summary guessing from page layer.

### Wave C: Render-Layer Closure

- Extract section-level render components.
- Pages consume VM only.
- Templates no longer interpret raw contracts.

### Wave D: Pattern Rollout

- Roll out to `HomeView`, `RecordView`, `SceneView`.

## 10. Acceptance Gates

- Gate 1: no business heuristics in core pages (keyword inference, field-combination inference, business-summary aggregation, action-group guessing).
- Gate 2: in strict mode, missing required contracts must produce explicit contract-missing signals (no silent business fallback).
- Gate 3: page layer must not consume `ui.contract.views.*` and raw deep structures directly; all must pass Contract Consumption Layer.
- Gate 4: runtime layer must not generate business copy or business semantics.
- Gate 5: `verify.scene.delivery.readiness` and strict-consumption checks must pass.

## 11. Mandatory Implementation Declaration

- Layer Target: `<Shell / Routing / Contracts / Runtime / Assemblers / Render>`
- Module: `<specific module path>`
- Reason: `<why this change and which boundary it enforces>`
- Input: `<upstream artifacts consumed>`
- Output: `<standardized downstream outputs>`
- Forbidden: `<responsibilities explicitly forbidden in this module>`

## 12. Non-Goals

- No new business features in this wave.
- No scene expansion in this wave.
- No new business interpretation in page layer.
- No business API access from render components.
- No new page-level heuristic compatibility logic.

## 13. Migration Success Criteria

This wave is considered complete when all are true:

1. `ActionView` is no longer the primary contract interpreter.
2. Page shell components only assemble and render.
3. Strict-mode truth is fully backend-driven.
4. Page VM is the only page-layer input.
5. `Contracts / Runtime / Assemblers` boundaries are clear and reusable.
6. The same pattern is replicable to `HomeView / RecordView / SceneView`.

## 14. Forbidden Shortcuts

- Do not reintroduce business heuristics in page layer “to make it run quickly”.
- Do not use frontend hardcoded scene sets as strict-policy source.
- Do not mask contract gaps with default business copy/grouping/summary.
- Do not do directory split without responsibility split.
- Do not turn assemblers into new super components/composables.
