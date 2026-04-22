# FE Internal Route Name Shell Shrink Z v1

## Goal

Shrink the remaining internal route-name compatibility shells in bounded
frontend surfaces.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: internal route-name shell shrink
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest bounded verify froze the residual compatibility boundary as
  private compat infrastructure plus internal route-name shells

## Planned Change

- add one shared helper for scene-first internal form/record navigation
- switch bounded internal `model-form` and `record` jumps to scene-first when
  scene identity can already be resolved
- keep existing compat route-name fallback only for unresolved cases

## Result

- `frontend/apps/web/src/app/sceneNavigation.ts`
  - added `resolveSceneFirstFormOrRecordLocation(...)` as a shared helper
  - helper resolves scene-first form/record targets from current `scene_key`,
    `action_id`, `menu_id`, `model`, and `record_id`, and only returns a scene
    route when scene identity is available
- `frontend/apps/web/src/views/ActionView.vue`
  - form-mode switch and list create now go scene-first before falling back to
    `name: 'model-form'`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
  - relation create-page open and post-create self replace now go scene-first
    before falling back to `name: 'model-form'`
- `frontend/apps/web/src/views/RecordView.vue`
  - suggested-action open-record and button-effect record navigation now go
    scene-first before falling back to `name: 'record'`
- `frontend/apps/web/src/components/view/ViewRelationalRenderer.vue`
  - relational row open now goes scene-first before falling back to
    `name: 'record'`
- residual internal route-name shells are now bounded to true fallback
  positions only; when current scene identity already exists, these flows no
  longer prefer compat route-name navigation

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-Z.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-INTERNAL-ROUTE-NAME-SHELL-SHRINK-Z.yaml docs/verify/fe_internal_route_name_shell_shrink_z_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/app/sceneNavigation.ts frontend/apps/web/src/views/ActionView.vue frontend/apps/web/src/pages/ContractFormPage.vue frontend/apps/web/src/views/RecordView.vue frontend/apps/web/src/components/view/ViewRelationalRenderer.vue`
  - PASS

## Decision

- PASS
- internal route-name compatibility shells have been further reduced in bounded
  frontend surfaces
- the remaining fallback route-name references are now explicitly fallback-only,
  not preferred navigation when scene identity is already present
