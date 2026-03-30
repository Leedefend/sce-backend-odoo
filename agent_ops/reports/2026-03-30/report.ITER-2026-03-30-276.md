# ITER-2026-03-30-276 Report

## Summary

- Removed frontend-invented list sort choices from the native list toolbar path.
- Kept current sort state visible as passive metadata instead of presenting unsupported interactive sort chips.
- Continued aligning the list surface with native Odoo metadata rather than frontend assumptions.

## Changed Files

- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts`
- `agent_ops/tasks/ITER-2026-03-30-276.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-276.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- Low
- Scope is frontend-only and subtractive.
- No backend contract or route changes were made.
- Existing sort state is still visible through passive toolbar text and subtitle.

## Rollback

```bash
git restore frontend/apps/web/src/components/page/PageToolbar.vue
git restore frontend/apps/web/src/pages/ListPage.vue
git restore frontend/apps/web/src/app/action_runtime/useActionViewDisplayComputedRuntime.ts
git restore agent_ops/tasks/ITER-2026-03-30-276.yaml
```

## Next Suggestion

- Continue consuming native search metadata on the list surface, especially search field hints and search-surface semantics that can replace generic frontend wording.
