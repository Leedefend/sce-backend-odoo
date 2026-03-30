# ITER-2026-03-30-292 Report

## Summary

- Added a passive sort-source label to the list toolbar.
- The label now distinguishes `原生默认排序` from `当前排序` using existing runtime/default-sort metadata only.
- No sort interaction or backend semantics changed.

## Changed Files

- `frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts`
- `frontend/apps/web/src/views/ActionView.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `agent_ops/tasks/ITER-2026-03-30-292.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-292.yaml`
- `pnpm -C frontend/apps/web typecheck:strict`

## Risk

- Low
- Frontend-only change.
- Read-only metadata clarification only.
- No new sort controls or backend coupling.

## Rollback

```bash
git restore frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts
git restore frontend/apps/web/src/views/ActionView.vue
git restore frontend/apps/web/src/pages/ListPage.vue
git restore frontend/apps/web/src/components/page/PageToolbar.vue
git restore agent_ops/tasks/ITER-2026-03-30-292.yaml
git restore docs/ops/iterations/delivery_context_switch_log_v1.md
```

## Next Suggestion

- Continue the native-metadata list usability line with the next safe enhancement that stays inside existing metadata and callback behavior.
