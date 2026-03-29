## Summary

- changed `AppShell` record-route title resolution so `project.project` detail pages no longer inherit the list-scene shell headline
- aligned record-route breadcrumb terminal label from generic record text to `项目详情` for project records
- kept the batch scoped to shell identity only; no button logic changed here

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-216.yaml`
- `frontend/apps/web/src/layouts/AppShell.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-216.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend shell batch
- scoped to record-route title and breadcrumb identity only
- no backend, schema, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-216.yaml`

## Next Suggestion

- refresh the project detail page and verify that the shell headline no longer shows `项目列表`; then continue narrowing the remaining top action-strip differences
