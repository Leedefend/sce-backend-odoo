# Route Convergence Entry Recheck Screen v1

## Goal

Re-evaluate the remaining entry-adjacent compatibility-route bridges after the
bounded frontend cleanup on `ModelListPage` and `MenuView`.

This recheck decides whether the remaining gap is still frontend-solvable or
whether it now depends on missing backend scene semantics.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: route convergence entry recheck
- Module Ownership: frontend route convergence proof boundary
- Kernel or Scenario: scenario
- Reason: the latest frontend cleanup reduced the known entry-adjacent bridges,
  so the next step is to classify the residual state without reopening a broad
  scan

## Recheck Basis

This recheck uses only:

- `route_convergence_compat_bridge_screen_v1.md`
- `route_convergence_entry_bridge_cleanup_g_v1.md`
- latest bounded code state of:
  - `frontend/apps/web/src/pages/ModelListPage.vue`
  - `frontend/apps/web/src/views/MenuView.vue`

## Recheck Result

### 1. The previously frozen scene-key-aware entry bridges are reduced

Observed updated state:

- `ModelListPage` now resolves a scene first from carried `scene_key`,
  `action_id`, `menu_id`, `model`, and `view_mode` before falling back to
  `name: 'action'`
- `MenuView` now resolves direct scene location from carried or menu-node
  `scene_key` before choosing any action-route fallback
- redirect branches in `MenuView` that already carry `scene_key` now go to the
  scene path or scene-registry fallback instead of landing on `name: 'action'`

Recheck decision:

- the scene-key-aware entry-adjacent bridges targeted by cleanup G are no
  longer the primary residual gap

### 2. The remaining residual gap is now concentrated in action-only entries

Observed bounded residual state:

- `ModelListPage` still falls back to `name: 'action'` when no scene can be
  derived from the carried context
- `MenuView` still falls back to `name: 'action'` for menu/action combinations
  where neither direct `scene_key` nor scene-registry authority matching can
  produce a scene target

Why this matters:

- these residual branches no longer fail because the frontend ignored an
  available scene hint
- they fail because the bounded runtime state still does not provide enough
  scene identity to collapse the action entry further

### 3. The next step is no longer a pure frontend bridge cleanup

Classification:

- the remaining residual branches are not just frontend route-choice issues
- they indicate action-only entry cases for which the current bounded frontend
  state cannot derive a unique scene
- further convergence on those paths would now depend on backend semantic
  supply, most likely at the scene-orchestration layer

## Final Decision

The strongest current statement is:

> entry-adjacent compatibility bridges have been further reduced on the
> frontend, and the remaining route-convergence gap is now concentrated in
> action-only entries that do not currently carry enough scene identity for the
> frontend to collapse them further.

Therefore:

- do not open another frontend-only cleanup batch immediately
- open a backend semantic-supply screen next if stronger route convergence is
  still required

## Frozen Next-Step Direction

If the team wants to continue route convergence, the next bounded batch should
move to backend battlefield and answer:

1. which action-only entries should emit scene identity directly
2. whether that identity belongs in business facts or scene orchestration
3. how the backend can supply that identity without reintroducing native menu or
   action contracts as frontend authority
