# Route Convergence Entry Bridge Cleanup G v1

## Goal

Reduce the remaining entry-adjacent compatibility-route bridges limited to:

- `ModelListPage` legacy redirect to `name: 'action'`
- `MenuView` branches that still land on `name: 'action'` even when a scene key
  is already carried

## Scope

- `frontend/apps/web/src/pages/ModelListPage.vue`
- `frontend/apps/web/src/views/MenuView.vue`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: route convergence entry bridge cleanup
- Module Ownership: ModelListPage + MenuView
- Kernel or Scenario: scenario
- Reason: route-convergence screen has classified these two points as the next
  frontend-solvable entry-adjacent bridge candidates

## Implemented Changes

- `ModelListPage` now tries scene-first resolution from the carried route query
  before falling back to the legacy action route, so list entry aligns with the
  existing scene registry when enough context is already present
- `MenuView` now recognizes carried `scene_key` or menu node `scene_key` as a
  stronger scene-oriented hint and routes to the scene path or scene registry
  fallback before any action-route fallback is chosen

## Result

- legacy list entry is now more clearly scene-first
- `MenuView` no longer prefers `name: 'action'` for branches that already carry
  scene-oriented identity
- internal compatibility-shell bridges remain unchanged in this batch
