# ITER-2026-03-30-294 Report

## Summary

- Aligned the list header subtitle with the toolbar sort-source semantics.
- Subtitle text now distinguishes between native default sort and current runtime sort using existing runtime labels.
- No new interactions or backend behavior were introduced.

## Changed Files

- `frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `agent_ops/tasks/ITER-2026-03-30-294.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-294.yaml`
- `pnpm -C frontend/apps/web typecheck:strict`

## Risk

- Low
- Frontend-only runtime helper change.
- No surface interaction changes.
- Uses existing runtime sort labels only.

## Rollback

```bash
git restore frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore agent_ops/tasks/ITER-2026-03-30-294.yaml
git restore docs/ops/iterations/delivery_context_switch_log_v1.md
```

## Next Suggestion

- Continue the native-metadata list usability line with the next low-risk metadata-derived enhancement.
