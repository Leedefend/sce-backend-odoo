# Scene Proof Fix Action/Form E v1

## Goal

Reduce direct action/model loader dependence in `ActionView` and
`ContractFormPage`.

This batch keeps contract loaders as bounded runtime mechanics, but makes scene
context the clearer primary input.

## Scope

- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `frontend/apps/web/src/api/contract.ts`

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: scene proof fix action/form
- Module Ownership: ActionView + ContractFormPage
- Kernel or Scenario: scenario
- Reason: reduce the proof gap frozen by the completion-proof audit without
  expanding into landing/menu/backend work

## Implemented Changes

- `api/contract` action loader now accepts additive `sceneKey` and forwards it
  to `ui.contract`, aligning action-based contract reads with existing
  scene-first context
- `ContractFormPage` now passes the current `sceneKey` through both action and
  model contract loading paths, so form contract reads no longer present as pure
  native action/model requests when scene context is already known
- `ActionView` now resolves current scene-ready entry by `sceneKey` first and
  only falls back to `actionId/menuId` target matching afterward, reducing the
  apparent primacy of native action identity inside the page model
