# Scene Proof Fix Landing/Menu F v1

## Goal

Reduce the remaining strict proof gaps limited to:

- landing `/a` fallback
- `resolveMenuAction(...)`-based menu-entry reconstruction

## Scope

- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/views/WorkbenchView.vue`
- `frontend/apps/web/src/app/resolvers/menuResolver.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: scene proof fix landing/menu
- Module Ownership: session + router + workbench + menu resolver
- Kernel or Scenario: scenario
- Reason: reduce the final proof blockers frozen by the recheck screen

## Implemented Changes

- `menuResolver` now exposes `resolveScenePathFromMenuResolve(...)`, which
  prefers direct scene identity and otherwise uses existing scene-registry
  authority matching before any action fallback is chosen
- `session.resolveCompatibilityMenuPath()` now uses that shared scene-first
  resolution, reducing landing `/a` fallback to cases where no scene can be
  derived
- router menu guard and Workbench menu-open flow now also reuse the same shared
  scene-first resolution path, reducing the remaining proof gap in
  `resolveMenuAction(...)`-rooted entry reconstruction
