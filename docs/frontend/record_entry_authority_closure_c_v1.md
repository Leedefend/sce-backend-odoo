# Record Entry Authority Closure C v1

## Goal

Lower the public authority of `/r/:model/:id` in ordinary frontend navigation.

This batch consumes backend additive `entry_target.record_entry` and keeps the
record route as a compatibility bridge only.

## Scope

- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- `frontend/apps/web/src/views/SceneView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/views/RecordView.vue`
- `frontend/apps/web/src/router/index.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: record entry authority closure C
- Module Ownership: scene registry + scene view + record contract consumer
- Kernel or Scenario: scenario
- Reason: consume backend scene-carried record-entry semantics before further
  native route cleanup

## Closure Rule

- `/r/:model/:id` remains compatibility-only
- ordinary record entry should redirect or render through `/s/:sceneKey` when
  one record_entry envelope can be resolved deterministically
- frontend must consume `record_entry` generically and must not introduce
  model-specific reopen rules

## Implemented Changes

- `sceneRegistry` now parses backend `entry_target.record_entry` and can resolve
  a scene by `scene_key/action_id/menu_id/model/record_id`
- router guard now intercepts ordinary `/r/:model/:id` entry, resolves the
  matching scene through backend scene authority data, and redirects to
  `/s/:sceneKey` with carried `model/record_id/action_id/menu_id` query context
- `SceneView` now prefers scene-local embedded record rendering when one
  `record_entry` envelope is available, instead of degrading ordinary record
  flows to `/r`
- `ContractFormPage` now reads `model/record_id` from scene query context as a
  generic fallback, so embedded record scenes no longer depend on native route
  params alone
- `RecordView` now reopens records through the current scene when `scene_key`
  context is already known, keeping `/r` as compatibility-only
