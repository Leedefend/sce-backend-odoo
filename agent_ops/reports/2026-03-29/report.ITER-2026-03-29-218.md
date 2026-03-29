## Summary

- fixed action-view row-click routing so `project.project` detail routes no longer inherit list-scene query identity
- explicitly clear `scene` and `scene_key` when navigating from list/action pages into `/r/project.project/:id`
- kept the batch scoped to project detail route query cleanup only

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-218.yaml`
- `frontend/apps/web/src/app/action_runtime/useActionViewNavigationRuntime.ts`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-218.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend navigation batch
- scoped to project record row-click query shaping only
- no backend, schema, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-218.yaml`

## Next Suggestion

- refresh the project list, click back into the same record, and verify the detail URL no longer carries `scene_key=projects.list`; then continue trimming any remaining top action-strip differences
