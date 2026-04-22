# FE Private Compat Emitter Shrink AH v1

## Goal

Shrink the remaining private compat emitters in bounded entry surfaces.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: private compat emitter shrink
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: router registration and sceneRegistry prefix recognition are already
  the dominant baseline, so the next bounded implementation should first shrink
  the remaining direct compat emitters in entry surfaces

## Result

- `frontend/apps/web/src/app/sceneNavigation.ts`
  - added `resolveSceneFirstActionLocation(...)` so bounded entry surfaces can
    resolve action-shaped targets to scenes before falling back to compat paths
- `frontend/apps/web/src/views/WorkbenchView.vue`
  - tile action and record targets now use scene-first navigation before
    falling back to `/compat/action` or `/compat/record`
- `frontend/apps/web/src/views/HomeView.vue`
  - workspace entry open, enterprise enablement target open, and related record
    handoff now use scene-first navigation before compat fallback
- `frontend/apps/web/src/views/MyWorkView.vue`
  - `openScene(...)` and `openRecord(...)` now prefer scene-first action/record
    handoff before falling back to `/compat/action` or `/compat/record`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - project intake handoff no longer routes through `/compat/form/.../new`; it
    now replaces directly to the scene path `/s/project.projects_intake`
- bounded entry surfaces no longer use private compat routes as preferred
  navigation; the remaining `/compat/...` strings in those files are fallback
  branches only

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-AH.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-AH.yaml docs/verify/fe_private_compat_emitter_shrink_ah_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/app/sceneNavigation.ts frontend/apps/web/src/views/WorkbenchView.vue frontend/apps/web/src/views/HomeView.vue frontend/apps/web/src/views/MyWorkView.vue frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - PASS

## Decision

- PASS
- direct private compat emitters were further reduced in bounded entry surfaces
- remaining private compat references in these files are now fallback-only
