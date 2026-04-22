# FE Action Producer Migration Implement DQ

## Goal

Reduce `/compat/action/...` production in the highest-visibility frontend
producers while preserving the restored bridge as fallback.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-FE-ACTION-PRODUCER-MIGRATION-IMPLEMENT-DQ.yaml`
   - PASS
2. `pnpm -C frontend/apps/web typecheck:strict`
   - PASS
3. `pnpm -C frontend/apps/web build`
   - PASS
   - Existing bundle-size warning only
4. `make frontend.restart`
   - PASS
   - Frontend ready at `http://127.0.0.1:5174/`
5. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-FE-ACTION-PRODUCER-MIGRATION-IMPLEMENT-DQ.yaml frontend/apps/web/src/views/HomeView.vue frontend/apps/web/src/views/WorkbenchView.vue frontend/apps/web/src/services/action_service.ts frontend/apps/web/src/app/sceneNavigation.ts docs/verify/fe_action_producer_migration_implement_dq_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
   - PASS

## Result

This batch narrows the bridge hit-rate instead of removing the bridge itself:

- `sceneNavigation.ts` now carries `view_mode` through `resolveSceneFirstActionLocation`
- `action_service.ts` now reuses the shared scene-first resolver instead of its
  own local copy
- `HomeView.vue` now feeds existing `targetModel` into scene-first action
  resolution and prefers scene-first even when an entry already carries a legacy
  `/a/...` or `/compat/action/...` route
- `WorkbenchView.vue` now treats legacy action route strings as candidates for
  scene-first upgrade before pushing raw route output

The compatibility bridge remains in place as bounded fallback when scene
resolution still cannot derive a stable scene path.
