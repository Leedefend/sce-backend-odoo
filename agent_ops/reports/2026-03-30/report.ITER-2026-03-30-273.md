# ITER-2026-03-30-273

## Summary
- Made the native list surface the single owner of contract-driven filter/group controls.
- Removed duplicated outer quick-filter/saved-filter/group-by blocks from `ActionView` when the page is already rendering a list surface.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-273.yaml`
- `frontend/apps/web/src/views/ActionView.vue`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-273.yaml`
- PASS: `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk
- Low.
- Frontend-only display ownership adjustment.
- Non-list surfaces keep their current outer contract blocks.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-273.yaml`
- `git restore frontend/apps/web/src/views/ActionView.vue`

## Next Suggestion
- Continue tightening list metadata-first behavior, especially remaining toolbar copy and search affordance details that still look generic rather than contract-native.
