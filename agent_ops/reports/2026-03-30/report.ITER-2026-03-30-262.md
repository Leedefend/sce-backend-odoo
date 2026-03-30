# ITER-2026-03-30-262

## Summary
- Fixed `ActionView` view-mode filtering so the real menu->action path can keep `tree + kanban` visible together.
- Preserved sidebar behavior and limited the change to the in-page action route.
- Kept the implementation generic and contract-driven.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-262.yaml`
- `frontend/apps/web/src/views/ActionView.vue`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-262.yaml`
- PASS: `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk
- Low.
- Change is limited to frontend view-mode visibility on the action page.
- No backend contract or sidebar behavior changed.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-262.yaml`
- `git restore frontend/apps/web/src/views/ActionView.vue`

## Next Suggestion
- Verify the real product route and, if the product path bypasses this component layer, continue tracing from the actual runtime entry.
