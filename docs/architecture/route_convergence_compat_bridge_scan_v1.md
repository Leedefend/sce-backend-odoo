# Route Convergence Compatibility Bridge Scan v1

## Goal

Collect the remaining compatibility-route bridge candidates for `/m`, `/a`,
`/r`, and `/f` after the scene-first proof chain has cleared its previously
frozen strict blockers.

This scan does not decide which candidates are acceptable long-term. It only
collects and groups them for the next bounded screen.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance scan
- Module: route convergence compatibility bridge
- Module Ownership: frontend route convergence proof boundary
- Kernel or Scenario: scenario
- Reason: compatibility route forms still exist after proof closure, so a
  bounded scan is needed before any stronger route-convergence claim or
  deprecation sequence is proposed

## Scan Basis

This scan uses only the current bounded frontend consumer state around:

- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/views/MenuView.vue`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/views/RecordView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/pages/ModelListPage.vue`
- `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue`

## Candidate Groups

### 1. Route registration candidates

Observed candidates:

- router still registers `/m/:menuId`
- router still registers `/a/:actionId`
- router still registers `/r/:model/:id`
- router still registers `/f/:model/:id`

Why they matter:

- these route forms still exist as public runtime shapes
- they are therefore the first candidates in any future convergence or
  deprecation line

This scan does not conclude whether they can be removed immediately.

### 2. Product-entry or cross-surface redirect candidates

Observed candidates:

- `ModelListPage.vue` still redirects legacy list entry to `name: 'action'`
- `MenuView.vue` still contains branches that fall back to `name: 'action'`
  when no scene location can be derived

Why they matter:

- these are closer to product-entry semantics than purely internal bridge
  mechanics
- if route convergence continues, these candidates need the next screen to
  decide whether they still represent true entry dependence or only bounded
  compatibility fallback

### 3. Compatibility-shell internal navigation candidates

Observed candidates:

- `ActionView.vue` still pushes `name: 'model-form'` when form mode takes over
- `ContractFormPage.vue` still pushes `name: 'model-form'` for create/return
  flows and still falls back to `name: 'action'` in bounded reopen branches
- `RecordView.vue` still pushes `name: 'action'` when no scene can be resolved,
  and still uses `name: 'record'` for record route continuity
- `ViewRelationalRenderer.vue` still opens relation rows through `name:
  'record'`

Why they matter:

- these candidates happen after the user is already inside compatibility-aware
  views or internal record/form flows
- they are likely different in removal priority from top-level entry routes
- the next screen must classify whether they are acceptable internal bridges or
  whether any of them still acts as a hidden product-entry dependency

### 4. Already reduced but still relevant normalization candidates

Observed candidates:

- `session.resolveCompatibilityMenuPath()` now normalizes legacy `/m` input to a
  scene path instead of emitting `/a`
- router menu guard now prefers `resolveScenePathFromMenuResolve(...)` before
  action fallback

Why they remain relevant:

- these are no longer primary blockers, but they define the current boundary of
  what "compatibility-only" means in the codebase
- the next screen should use them as the baseline when deciding which residual
  route forms are still real convergence work

## Scan Output

This scan freezes the candidate set for the next screen as:

1. route registration surface: `/m`, `/a`, `/r`, `/f`
2. entry-adjacent fallbacks: `ModelListPage`, `MenuView`
3. compatibility-shell internal route mechanics: `ActionView`,
   `ContractFormPage`, `RecordView`, `ViewRelationalRenderer`
4. normalization baseline: `session` + router shared scene-first menu
   resolution

## Frozen Next-Step Direction

Open a bounded screen next to classify:

- which candidates are still product-entry dependencies
- which candidates are acceptable compatibility-shell internals
- which candidates would need backend semantic supply before further frontend
  convergence is safe
