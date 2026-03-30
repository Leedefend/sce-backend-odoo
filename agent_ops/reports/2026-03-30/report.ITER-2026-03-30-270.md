# ITER-2026-03-30-270

## Summary
- Continued the Odoo-native metadata usability line on the frontend list surface.
- Reused existing contract-driven quick filters, saved filters, and group-by metadata instead of leaving the native list path on a fixed toolbar.
- Kept the change generic and frontend-only.

## Changed Files
- `agent_ops/tasks/ITER-2026-03-30-270.yaml`
- `frontend/apps/web/src/components/page/PageToolbar.vue`
- `frontend/apps/web/src/pages/ListPage.vue`
- `frontend/apps/web/src/views/ActionView.vue`

## Verification
- PASS: `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-270.yaml`
- PASS: `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk
- Low.
- Frontend-only contract consumer change.
- No backend contract semantics changed.
- Existing list search/sort/filter controls remain in place; contract-driven chips are additive.

## Rollback
- `git restore agent_ops/tasks/ITER-2026-03-30-270.yaml`
- `git restore frontend/apps/web/src/components/page/PageToolbar.vue`
- `git restore frontend/apps/web/src/pages/ListPage.vue`
- `git restore frontend/apps/web/src/views/ActionView.vue`

## Next Suggestion
- Refresh the current project list page and verify that the native list surface now shows contract-driven quick filters, saved filters, and group-by controls.
