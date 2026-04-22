# Frontend Three-Layer Contract Governance Topic v1

Status: Governance Topic  
Scope: `AppShell -> SceneView -> ListPage` consumption boundary for high-frequency work pages such as `projects.list`

## 1. Purpose

This topic freezes the frontend contract-consumption boundary required to
converge the duplicated top structure on `projects.list`.

The problem is no longer "the spacing is a little off". The problem is that
the frontend currently renders top-area semantics from three different layers
without a hard mutual-exclusion rule:

```text
AppShell
  + SceneView
  + ListPage
  -> repeated top structure
```

Without a frozen consumption boundary, the repository will keep repeating the
same failure shape:

- shell-level title or breadcrumb remains visible above the page work-surface
- scene-level actions or view switches add a second top strip
- list-level toolbar renders a third strip for the same work page

This topic defines:

- what each layer is allowed to consume
- what each layer is forbidden to infer
- which semantics are mutually exclusive across layers
- which current behaviors are violations
- the only valid follow-up batch order

## 2. Existing Contract References

This topic reuses and sharpens these existing boundaries:

- [App Shell Contract vs Page Scene Contract v1](/mnt/e/sc-backend-odoo/docs/architecture/app_shell_vs_page_scene_contract_v1.md)
- [Backend Contract Layer Responsibility Freeze v1](/mnt/e/sc-backend-odoo/docs/architecture/backend_contract_layer_responsibility_freeze_v1.md)
- [UI Base Contract vs Scene-ready Contract v1](/mnt/e/sc-backend-odoo/docs/architecture/ui_base_vs_scene_ready_contract_v1.md)
- [原生视图复用驱动的前端页面设计规范 v1](/mnt/e/sc-backend-odoo/docs/architecture/native_view_reuse_frontend_spec_v1.md)

## 3. Current Fact Map

### 3.1 AppShell Consumption Facts

Primary consumer:

- [AppShell.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/layouts/AppShell.vue)

Actual inputs today:

- `session.roleSurface`
- `session.scenes` via `getSceneByKey(sceneKey)`
- `session.currentAction`
- navigation tree / active menu path
- route metadata such as `sceneSubtitle`, `sceneHeaderMode`, `sceneAnchorLine`

Current visible outputs:

- breadcrumb
- shell page title
- shell subtitle / anchor line
- global navigation shell

Important fact:

- AppShell does not consume the page contract as its primary truth source.
- AppShell title mostly comes from `scene.label`, menu path, or action meta.
- AppShell breadcrumb is built from the navigation tree, not from page-level
  scene blocks.

### 3.2 SceneView Consumption Facts

Primary consumer:

- [SceneView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/SceneView.vue)

Actual inputs today:

- `usePageContract('scene')`
- scene registry entry from `getSceneByKey(sceneKey)`
- route context

Current visible outputs:

- scene header actions from `pageContract.globalActions`
- scene loading / error / forbidden / runtime diagnostics
- scene-level view switch chips

Important fact:

- `headerActions` are contract-backed
- `sceneViewSwitchOptions` are not contract-backed today
- current `projects.list <-> projects.ledger` view-switch map is a frontend
  hardcoded rule in `SceneView.vue`

### 3.3 ListPage Consumption Facts

Primary consumer path:

- [ActionView.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/views/ActionView.vue)
- [useActionPageModel.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts)
- [ListPage.vue](/mnt/e/sc-backend-odoo/frontend/apps/web/src/pages/ListPage.vue)

Actual inputs today:

- `vm.page.title`
- `vm.page.subtitle`
- `vm.page.sceneKey`
- `listProfile`
- quick filters / saved filters / group-by / search menu surfaces
- status and pagination state
- primary action label / handler

Important facts:

- `listProfile` is sourced first from `scene_contract_v1`, then from
  `sceneRegistry.list_profile`
- `ListPage` does not request backend data directly; it consumes assembled page
  state from `ActionView`
- `vm.page.subtitle` is frontend-composed from record count and sort label
  rather than delivered as a backend fact

## 4. Frozen Three-Layer Boundary

### 4.1 AppShell Layer

Allowed inputs:

- app shell contract
- role surface
- default route
- navigation tree
- active scene identity
- shell-only diagnostic metadata

Allowed outputs:

- shell navigation
- shell breadcrumb
- shell identity / role / environment context

Forbidden:

- rendering page work-surface controls
- rendering list search / filter / group / sort / pagination controls
- rendering scene action bars for high-frequency work pages
- inferring business page subtitle from frontend heuristics

Hard rule:

> AppShell may identify the page, but it may not compete with the page for the
> visible work-surface header.

### 4.2 SceneView Layer

Allowed inputs:

- scene page contract
- scene diagnostics
- scene permissions
- scene-level actions explicitly provided by contract

Allowed outputs:

- scene status / validation / forbidden / runtime diagnostic surfaces
- scene-level actions only when they are not already owned by the work-surface

Forbidden:

- hardcoded view-switch rules
- repeating the list work-surface title
- creating a second toolbar when the page work-surface already owns actions
- inventing scene navigation chips not declared by backend semantics

Hard rule:

> SceneView may orchestrate a scene, but it may not fabricate page-level
> controls or duplicate a work-surface toolbar.

### 4.3 ListPage Layer

Allowed inputs:

- list work-surface contract assembled from action/scene semantic inputs
- list columns / filter / group / sort / pagination / primary action surfaces
- page-level status and record-count display inputs

Allowed outputs:

- the only visible list work-surface toolbar
- list title when the page owns the title
- search / filter / group / sort / pagination / batch controls

Forbidden:

- deriving business semantics that backend did not supply
- inventing fallback business subtitles
- repeating scene-level navigation or shell-level breadcrumb semantics

Hard rule:

> ListPage is the only layer allowed to render the list work-surface toolbar.

## 5. Mutual-Exclusion Rules

These rules are mandatory for all high-frequency work pages and especially for
`projects.list`.

### 5.1 Title Ownership

- If ListPage owns the work-surface title, AppShell must not render a second
  visible work title above it.
- If AppShell renders only breadcrumb/identity, it must stay shell-only and not
  behave like a page header.

### 5.2 Action Ownership

- If scene actions are promoted into the list work-surface toolbar, SceneView
  must not render a second action strip.
- If SceneView keeps an action strip, ListPage must not repeat the same action
  semantics.

### 5.3 View Switch Ownership

- View-switch controls must come from backend semantics.
- Frontend hardcoded scene-switch maps are forbidden as a long-term behavior.
- A page may show view switches only if the backend explicitly supplies that
  surface.

### 5.4 Subtitle Ownership

- Record-count / sort display is a work-surface concern.
- Business subtitle or business guidance is not allowed to be composed by
  shell-level heuristics.
- If no backend subtitle exists, the page may remain without a subtitle.

## 6. Current Violation Inventory

### 6.1 Confirmed Violations

1. `SceneView` currently hardcodes `PROJECT_SCENE_SWITCH_MAP`.
   Classification:
   - `FRONTEND_OVER_DERIVE`

2. `ListPage` subtitle is frontend-generated from record count and sort source.
   Classification:
   - `FRONTEND_OVER_DERIVE`
   Note:
   - acceptable as a temporary display metric only if it is reclassified as
     pure UI chrome and does not pretend to be business guidance

3. `projects.list` top structure is currently rendered by three layers:
   `AppShell`, `SceneView`, and `ListPage`.
   Classification:
   - `LAYER_OVERLAP`

### 6.2 Structural Risk

Even when each layer individually looks "reasonable", the combined result is
still invalid if the user sees multiple competing top strips for the same work
surface.

## 7. Convergence Strategy

The convergence must happen in four sequential batches.

### Batch A: Contract Surface Freeze

Goal:

- define the exact backend-facing surface for:
  - shell layer
  - scene layer
  - list work-surface layer

Must output:

- allowed fields per layer
- forbidden frontend inference list
- ownership map for title / actions / view-switch / subtitle

### Batch B: Violation Closure Screen

Goal:

- check current `projects.list` implementation against this topic doc

Must output:

- per-element ownership matrix
- contract-backed vs frontend-derived inventory
- keep/remove/migrate decision for each top element

### Batch C: Backend Semantic Supply

Goal:

- if view-switch or scene-to-list control ownership still needs explicit
  semantics, backend must supply them

Hard rule:

- frontend must not solve missing scene/list switching semantics by local maps

### Batch D: Frontend Structural Convergence

Goal:

- remove duplicated top rendering according to the ownership matrix

Hard rule:

- this batch may only consume already-frozen semantics from the previous
  batches

## 8. Stop Conditions

Stop immediately if any of the following happens during follow-up execution:

- a layer tries to consume fields not declared for it
- a frontend implementation proposes a new hardcoded business or scene rule
- scene/list ownership cannot be decided from frozen contract semantics
- backend semantic supply is missing but frontend attempts to compensate

## 9. One-Line Governance Rule

For `projects.list`, the frontend may show only one visible work-surface top
bar, and every visible control in that bar must have a declared contract owner.
