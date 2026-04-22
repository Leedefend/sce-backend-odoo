# Scene Entry Authority Closure A v1

## Goal

Lower the public authority of `/m/:menuId` in ordinary frontend navigation.

This batch does not remove the compatibility route itself. It removes ordinary
product-flow dependence on that route where the frontend already has enough
scene-first information to navigate directly.

## Scope

- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/views/WorkbenchView.vue`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: scene entry authority closure A
- Module Ownership: router + session + workbench navigation
- Kernel or Scenario: scenario
- Reason: reduce one parallel public route family without reopening page-local
  semantics or backend contract scope

## Closure Rule

- `/m/:menuId` remains compatibility-only
- default landing and workbench first-entry behavior must prefer scene-first
  targets instead of pushing through `/m/:menuId`
- if scene-first target cannot be derived, degrade to existing fallback rather
  than inventing new frontend business routing logic

## Implemented Changes

- router guard now resolves `/m/:menuId` into scene-first or action fallback
  before the compatibility component becomes the ordinary product path
- session landing-path resolution now normalizes legacy `/m/:menuId` defaults
  into scene/action targets when the navigation tree already provides them
- workbench first-entry and menu-fallback actions now navigate directly to
  resolved scene/action targets instead of first bouncing through `/m/:menuId`
