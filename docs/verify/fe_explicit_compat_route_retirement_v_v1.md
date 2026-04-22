# FE Explicit Compat Route Retirement V v1

## Goal

Retire the remaining explicit public compatibility route prefixes `/a /f /r`
while preserving current internal route names.

## Fixed Architecture Declaration

- Layer Target: Frontend contract-consumer runtime
- Module: explicit compatibility route retirement
- Module Ownership: frontend scene-first entry authority
- Kernel or Scenario: scenario
- Reason: the latest bounded classification froze the remaining compatibility
  route forms as primarily concentrated at explicit `/a /f /r` registration
  level

## Planned Change

- migrate explicit public compat prefixes to private compat prefixes
- preserve internal route names `action`, `model-form`, `record`
- update direct path builders and prefix detectors consistently

## Result

- `frontend/apps/web/src/router/index.ts`
  - explicit public compatibility registrations moved from `/a /f /r` to
    private compatibility prefixes:
    - `/compat/action/:actionId`
    - `/compat/form/:model/:id`
    - `/compat/record/:model/:id`
  - route names `action`, `model-form`, and `record` were preserved
- direct path builders and prefix detectors were aligned to the private
  compatibility prefixes across:
  - `sceneRegistry`
  - `AppShell`
  - `WorkbenchView`
  - `action_service`
  - `SceneView`
  - `useNavigationMenu`
  - `suggested_action/runtime`
  - `HomeView`
  - `CapabilityMatrixView`
  - `MyWorkView`
  - `useActionViewActionMetaRuntime`
  - `ProjectsIntakeView`
- public `/a /f /r` prefixes no longer remain in the bounded frontend runtime
  surface

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-EXPLICIT-COMPAT-ROUTE-RETIREMENT-V.yaml`
  - PASS
- `pnpm -C frontend/apps/web typecheck:strict`
  - PASS
- `pnpm -C frontend/apps/web build`
  - PASS
  - note: existing chunk-size warning only
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-EXPLICIT-COMPAT-ROUTE-RETIREMENT-V.yaml docs/verify/fe_explicit_compat_route_retirement_v_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md frontend/apps/web/src/router/index.ts frontend/apps/web/src/app/resolvers/sceneRegistry.ts frontend/apps/web/src/layouts/AppShell.vue frontend/apps/web/src/views/WorkbenchView.vue frontend/apps/web/src/services/action_service.ts frontend/apps/web/src/views/SceneView.vue frontend/apps/web/src/composables/useNavigationMenu.ts frontend/apps/web/src/app/suggested_action/runtime.ts frontend/apps/web/src/views/HomeView.vue frontend/apps/web/src/views/CapabilityMatrixView.vue frontend/apps/web/src/views/MyWorkView.vue frontend/apps/web/src/app/action_runtime/useActionViewActionMetaRuntime.ts frontend/apps/web/src/views/ProjectsIntakeView.vue`
  - PASS

## Decision

- PASS
- the explicit public compatibility route prefixes `/a /f /r` have been retired
  in the bounded frontend runtime
- internal route names remain available, but they now resolve through private
  compatibility prefixes only
