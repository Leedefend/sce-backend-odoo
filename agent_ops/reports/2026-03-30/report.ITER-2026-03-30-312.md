# ITER-2026-03-30-312 Report

## Summary

- Replaced raw native sort tokens with user-readable sort labels.
- Native default sort text now uses existing contract column labels plus readable direction text.
- Subtitle, toolbar summary, and active-condition chips now share the same readable sort wording.

## Changed Files

- `frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-312.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-312.yaml`
- `pnpm -C frontend/apps/web typecheck:strict`

## Risk

- Low
- Frontend-only display cleanup.
- Reuses existing contract column labels.
- No sort behavior or backend semantics changed.

## Rollback

```bash
git restore frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/tasks/ITER-2026-03-30-312.yaml
git restore docs/ops/iterations/delivery_context_switch_log_v1.md
```

## Next Suggestion

- Rebuild the frontend and visually verify the readable default-sort wording on the project list page.
