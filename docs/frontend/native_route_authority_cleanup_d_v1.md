# Native Route Authority Cleanup D v1

## Goal

Reduce remaining ordinary action-route navigation in `MenuView` and
`RecordView`.

This batch only uses already available scene-first contract output and keeps
`/a/:actionId` as a compatibility bridge.

## Scope

- `frontend/apps/web/src/views/MenuView.vue`
- `frontend/apps/web/src/views/RecordView.vue`
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: native route authority cleanup D
- Module Ownership: MenuView + RecordView
- Kernel or Scenario: scenario
- Reason: remove the remaining ordinary action-route navigation edges frozen by
  the audit screen

## Implemented Changes

- `MenuView` now resolves a scene by existing `action_id/menu_id` authority
  before falling back to `name: 'action'`, so leaf and redirect branches prefer
  direct scene-first navigation when the registry already knows the scene
- `RecordView` now routes button-driven, response-driven, and effect-driven
  action opens through a shared scene-first helper, only using `name: 'action'`
  when no scene can be resolved from existing contract-consumer state
