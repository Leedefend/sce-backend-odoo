# Scene Entry Authority Closure B v1

## Goal

Lower the public authority of `/a/:actionId` in ordinary frontend navigation.

This batch uses the backend additive `entry_target` surface and current scene
registry targets to resolve a scene-oriented entry before the action route
becomes the main public URL.

## Scope

- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: scene entry authority closure B
- Module Ownership: router + scene registry authority resolution
- Kernel or Scenario: scenario
- Reason: consume backend scene-oriented entry authority before further route
  cleanup

## Closure Rule

- `/a/:actionId` remains compatibility-only
- ordinary action entry should redirect to `/s/:sceneKey` when the scene can be
  resolved deterministically
- `/r` remains out of scope in this batch because embedded record carry still
  needs a separate bounded fix

## Implemented Changes

- `sceneRegistry` now parses backend additive `target.entry_target` and exposes
  `findSceneByEntryAuthority` so frontend can resolve a scene from
  `scene_key/action_id/menu_id/model/view_mode` without reintroducing
  model-specific routing rules
- router guard now intercepts `/a/:actionId` after `system.init`, resolves the
  matching scene through registry authority data, and redirects ordinary entry
  traffic to `/s/:sceneKey` while preserving compatibility query context
- ambiguity is kept fail-closed: when action authority cannot resolve to a
  single scene, frontend stays on the legacy compatibility route instead of
  inventing a new special case
