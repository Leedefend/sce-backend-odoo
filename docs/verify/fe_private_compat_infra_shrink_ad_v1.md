# FE Private Compat Infra Shrink AD v1

## Goal

Shrink the remaining private compat infrastructure in bounded frontend runtime
surfaces.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: private compat infrastructure shrink
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest bounded verify froze private compat infrastructure as the
  dominant residual compatibility boundary

## Planned Change

- target router registration, prefix recognition, and generic compat dispatch
- keep scene-first behavior as the only preferred navigation path
- avoid reopening backend semantic work or unrelated frontend shells

## Result

- `frontend/apps/web/src/services/action_service.ts`
  - `openAction(...)` and `openForm(...)` now resolve scene-first via
    `findSceneByEntryAuthority(...)` before falling back to private
    `/compat/action` or `/compat/record`
- `frontend/apps/web/src/composables/useNavigationMenu.ts`
  - `/native/action/:id` normalization now first resolves a scene route from
    `actionId`; only unresolved cases still rewrite to `/compat/action/:id`
- `frontend/apps/web/src/app/suggested_action/runtime.ts`
  - `open_project`, `open_action`, and `open_record` suggested actions now try
    scene-first navigation before falling back to `/compat/action` or
    `/compat/record`
- `frontend/apps/web/src/views/SceneView.vue`
  - workspace action targets and the bounded `target.action_id && !menuTree`
    record case no longer bridge to `/compat/action/...`; they now stay on the
    current scene route with embedded `action_id/menu_id/scene_key` query state
- dominant private compat infrastructure has been reduced from active dispatch
  sources to narrower fallback-only positions plus router/registry baseline

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-INFRA-SHRINK-AD.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-INFRA-SHRINK-AD.yaml docs/verify/fe_private_compat_infra_shrink_ad_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts frontend/apps/web/src/app/resolvers/sceneRegistry.ts frontend/apps/web/src/services/action_service.ts frontend/apps/web/src/views/SceneView.vue frontend/apps/web/src/composables/useNavigationMenu.ts frontend/apps/web/src/app/suggested_action/runtime.ts`
  - PASS

## Decision

- PASS
- active private compat infrastructure has been further reduced in bounded
  frontend surfaces
- remaining private compat references are now more clearly concentrated at
  router registration, scene-registry prefix recognition, and true unresolved
  fallback positions
