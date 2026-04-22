# Frontend Three-Layer Violation Closure Screen v1

Status: Governance Screen  
Scope: visible top-area elements on `projects.list`

## 1. Purpose

This screen turns the three-layer governance topic into a concrete execution
table.

It does not change frontend code.

It answers only one question:

> For every currently visible top-area element on `projects.list`, which layer
> owns it, what contract authorizes it, and should it be kept, removed, or
> migrated?

## 2. Evidence Base

Primary screenshot evidence:

- [project-list.png](/mnt/e/sc-backend-odoo/artifacts/playwright/high_frequency_pages_v2/20260419T074303Z/project-list.png)

Reference topic:

- [frontend_three_layer_contract_governance_topic_v1.md](/mnt/e/sc-backend-odoo/docs/architecture/frontend_three_layer_contract_governance_topic_v1.md)

## 3. Visible Top-Area Inventory

The current visible `projects.list` top area contains these user-visible
elements:

1. App shell breadcrumb chip row
2. Scene header action strip
3. Scene-level view switch chips
4. List work-surface title and record count
5. List search box and search menu toggle
6. List filter / group / sort / pagination controls
7. List primary action button

## 4. Ownership Matrix

| Visible element | Current renderer | Current source | Contract-backed? | Owner layer by rule | Decision | Follow-up batch |
| --- | --- | --- | --- | --- | --- | --- |
| App shell breadcrumb chip row | `AppShell` | navigation tree / active menu path | shell-backed | `AppShell` | `KEEP_WITH_SCOPE_LIMIT` | frontend structural convergence |
| Scene header action strip | `SceneView` | `pageContract.globalActions` | yes | `SceneView` only if not duplicated by work-surface | `MIGRATE_OR_MERGE` | backend semantic supply + frontend structural convergence |
| Scene view switch chips | `SceneView` | hardcoded `PROJECT_SCENE_SWITCH_MAP` | no | no current valid owner | `REMOVE_OR_BACKEND_SUPPLY` | backend semantic supply |
| List title + record count | `ListPage` | `vm.page.title` + record count state | partially | `ListPage` | `KEEP` | none |
| List subtitle-like metric text | `ListPage` | frontend-composed record/sort string | no business contract | `ListPage` only as pure UI metric | `RECLASSIFY_OR_DROP` | frontend structural convergence |
| List search box and search menu | `ListPage` | list work-surface inputs | yes | `ListPage` | `KEEP` | none |
| List filter/group/sort/pagination strip | `ListPage` | list work-surface inputs | yes | `ListPage` | `KEEP` | none |
| List primary action | `ListPage` | assembled page action input | yes | `ListPage` | `KEEP` | none |

## 5. Element-by-Element Decisions

### 5.1 App Shell Breadcrumb Chip Row

Current state:

- visible above the list work-surface
- built from navigation tree path
- shell-owned, not page-contract-owned

Decision:

- `KEEP_WITH_SCOPE_LIMIT`

Reason:

- breadcrumb is a shell navigation affordance, not a duplicated list toolbar
- it may remain only if it stays visually secondary and does not expand into a
  page header or action strip

### 5.2 Scene Header Action Strip

Current state:

- rendered by `SceneView`
- contract-backed through `pageContract.globalActions`
- currently occupies the same top work-surface band that `ListPage` already
  uses for search, filter, sort, and pagination

Decision:

- `MIGRATE_OR_MERGE`

Reason:

- contract-backed actions are valid semantics
- but `projects.list` may not show both a scene action strip and a list
  work-surface toolbar as separate bands

Required resolution:

- either backend marks these actions as work-surface actions
- or frontend merges them into the single list toolbar

### 5.3 Scene View Switch Chips

Current state:

- rendered by `SceneView`
- not backed by backend contract
- hardcoded in frontend via `PROJECT_SCENE_SWITCH_MAP`

Decision:

- `REMOVE_OR_BACKEND_SUPPLY`

Reason:

- current implementation violates the no-frontend-inference rule
- it has no valid long-term owner until backend semantic supply exists

Required resolution:

- if the product still needs a scene/list switch, backend must supply an
  explicit switch surface
- otherwise remove this strip completely

### 5.4 List Title and Record Count

Current state:

- rendered by `ListPage`
- page-level title is the correct work-surface anchor
- count is a work-surface metric

Decision:

- `KEEP`

Reason:

- this is the correct owner layer for the list work-surface header

### 5.5 List Subtitle-Like Metric Text

Current state:

- frontend currently composes subtitle-style text from records and sort labels
- not a backend business fact

Decision:

- `RECLASSIFY_OR_DROP`

Reason:

- it may exist only as pure UI chrome
- it must not masquerade as backend business guidance
- if it contributes visible noise, it should be dropped from high-frequency
  list pages

### 5.6 List Search / Filter / Group / Sort / Pagination / Primary Action

Current state:

- all are rendered inside the list work-surface toolbar
- all belong to the list work-surface layer

Decision:

- `KEEP`

Reason:

- these controls are the only valid primary top bar for `projects.list`

## 6. Closure Rules

`projects.list` may converge only if all of the following become true:

1. There is exactly one visible work-surface toolbar band.
2. Scene-level chips are either contract-backed and merged into the work
   surface, or removed.
3. AppShell stays shell-only and visually secondary.
4. No frontend-hardcoded scene switching remains.
5. No business-style subtitle is emitted without backend ownership.

## 7. Follow-Up Batch Assignment

### Batch C1: Backend Semantic Supply Screen

Goal:

- decide whether `projects.list` still needs scene/list switching semantics

Question to settle:

- should backend expose a switch surface for `projects.list <-> projects.ledger`
  at all?

### Batch C2: Backend Semantic Supply Implement

Goal:

- if switching is still needed, backend supplies the canonical scene switch
  surface and action ownership surface

### Batch D1: Frontend Structural Convergence

Goal:

- remove the second top band
- merge scene actions into the single work-surface toolbar when allowed by
  frozen semantics
- delete the hardcoded scene switch if backend does not supply a replacement

### Batch D2: Final Visual Verify

Goal:

- re-run the screenshot walkthrough and verify that only one primary top bar
  remains on `projects.list`

## 8. One-Line Execution Rule

For `projects.list`, any visible top-area element without a declared contract
owner must be removed or migrated before the page is considered converged.
