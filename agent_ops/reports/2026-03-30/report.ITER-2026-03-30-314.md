# ITER-2026-03-30-314 Report

## Summary

- Split list sort state into two tracks:
  - raw Odoo order token for all request/runtime paths
  - user-readable display label for subtitle, toolbar, and active-condition UI
- Fixed the regression where readable sort text like `id 升序` leaked into `api.data` requests.

## Changed Files

- `frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts`
- `frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-314.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-314.yaml`
- `pnpm -C frontend/apps/web typecheck:strict`

## Risk

- Low
- Frontend-only runtime wiring fix.
- Keeps readable sort wording in the UI.
- Restores valid raw order tokens for backend requests.

## Rollback

```bash
git restore frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts
git restore frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/tasks/ITER-2026-03-30-314.yaml
git restore docs/ops/iterations/delivery_context_switch_log_v1.md
```

## Next Suggestion

- Rebuild the frontend and verify the project list no longer sends localized sort text as the `order` payload.
