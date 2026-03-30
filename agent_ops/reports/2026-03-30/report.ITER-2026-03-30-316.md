# ITER-2026-03-30-316 Report

## Summary

- Added a frontend fallback label map for common Odoo system fields used in list sorting.
- Default sort wording no longer falls back to raw keys like `write_date` when the field is not present in visible columns.

## Changed Files

- `frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts`
- `agent_ops/tasks/ITER-2026-03-30-316.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-316.yaml`
- `pnpm -C frontend/apps/web typecheck:strict`

## Risk

- Low
- Frontend-only presentation fallback.
- Request order tokens remain unchanged.

## Rollback

```bash
git restore frontend/apps/web/src/app/action_runtime/useActionViewSurfaceDisplayRuntime.ts
git restore agent_ops/tasks/ITER-2026-03-30-316.yaml
git restore docs/ops/iterations/delivery_context_switch_log_v1.md
```

## Next Suggestion

- Rebuild the frontend and verify that default sort now reads as `更新时间 降序` instead of `write_date 降序`.
