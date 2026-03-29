## Summary

- made generic list routes in `ActionView` prefer the existing `ListPage` core by suppressing non-essential pre-table contract sections
- hid header action chips plus route-preset, focus, strict-alert, quick-filter, saved-filter, group-view, group-summary, and quick-action blocks when the page content kind is `list`
- kept the change generic to all list routes; `project.project` remains only the first validation sample

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-221.yaml`
- `frontend/apps/web/src/views/ActionView.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-221.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend list-shell batch
- scoped to list-route surface reduction only
- no backend, schema, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-221.yaml`

## Next Suggestion

- refresh the project list and verify that the page now leads with the native list core; then continue with detail-page structure parity using the same fact-first strategy
