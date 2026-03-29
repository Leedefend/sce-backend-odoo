## Summary

- normalized cached nav nodes to always expose `key/name/label/title`
- made `sceneRegistry` accept label/title-only scene payloads and alias same-route home-family scenes
- stopped hydrating the runtime scene registry from cached `sceneReadyContractV1` during `restore()`
- removed duplicate-route as a hard validator failure and replaced dev logging with expanded issue details

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-194.yaml`
- `frontend/apps/web/src/stores/session.ts`
- `frontend/apps/web/src/components/MenuTree.vue`
- `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
- `frontend/apps/web/src/app/resolvers/sceneRegistryCore.js`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-194.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && python3 agent_ops/scripts/frontend_verify_gate.py --frontend-dir frontend/apps/web --expect-status PASS'`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk, additive frontend compatibility only
- no backend contract rename/remove
- no ACL, schema, or business semantics change

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-194.yaml`

## Next Suggestion

- start a new iteration for `page contract -> frontend rendering` on one real scene page, focusing on fields/blocks/actions/readonly behavior from backend contract
