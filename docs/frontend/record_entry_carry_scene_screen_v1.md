# Record Entry Carry Scene Screen v1

## Goal

Determine whether `/r/:model/:id` can already be reduced from public authority
to a scene-oriented compatibility route, or whether backend semantic supply must
precede that convergence.

## Scope

Focused screening only:

- `frontend/apps/web/src/views/SceneView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/views/RecordView.vue`

This batch does not modify runtime behavior.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration screen
- Module: record entry carry authority screen
- Module Ownership: frontend route consumer boundary
- Kernel or Scenario: scenario
- Reason: decide whether record identity is already supplied as generic
  scene-carried semantics, or still depends on native route params

## Screen Findings

### 1. ContractFormPage still treats route params as record authority

- `ContractFormPage` computes `recordId` from `route.params.id` only
- no generic fallback from scene query or scene target context is consumed there
- this means embedded scene rendering can reuse the page only when the record id
  remains present as a native route authority

### 2. SceneView still degrades record scenes to `/r`

- for `layout.kind === 'record'`, `SceneView` can embed via
  `embeddedRecordActionId`, but the fallback path for concrete record identity
  still redirects to `/r/${model}/${recordId}`
- list/ledger flows also redirect to `/r` when `target.model + target.record_id`
  appear
- current scene query carry preserves `action_id/menu_id/scene_key`, but it does
  not establish one generic record-id contract for `ContractFormPage`

### 3. RecordView still treats `/r` as the canonical reopen path

- `RecordView` pushes `name: 'record'` with `model/id`
- this confirms record identity is still modeled as a native route family, not
  as a scene-carried semantic envelope

## Decision

`/r` is not yet eligible for the same closure pattern used for `/m` and `/a`.

The blocker is not a frontend-only routing tweak. The missing piece is a generic
record-entry semantic carrier that SceneView and ContractFormPage can both
consume without relying on `route.params.id`.

## Backend Layer Decision

The next supply task belongs to the `scene-orchestration layer`, not the
business-fact layer.

Reason:

- the missing data is not new business truth
- the missing data is the consumption-ready organization of existing record
  identity into one scene-carried contract surface
- backend should supply a bounded scene-oriented record-entry envelope, and
  frontend should consume that envelope generically instead of inventing
  model-specific route exceptions

## Frozen Next-Step Rule

- do not reduce `/r` public authority before one bounded backend semantic-supply
  batch defines the generic record-entry carry contract
- that next batch should state how `scene_key`, `record_id`, `model`, and
  optional compatibility refs are carried through scene entry without forcing
  `ContractFormPage` to depend on native route params
