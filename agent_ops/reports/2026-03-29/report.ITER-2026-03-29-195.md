## Summary

- projected `scene_contract_v1.permissions` and `diagnostics.consumer_runtime` into `ContractFormPage`
- added a visible runtime status panel for readonly/restricted form states
- disabled save/create actions when backend scene runtime denies write/create
- surfaced disabled reasons on primary save/create buttons
- made field rendering readonly when scene runtime blocks persistence

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-195.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-195.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && python3 agent_ops/scripts/frontend_verify_gate.py --frontend-dir frontend/apps/web --expect-status PASS'`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk frontend-only contract consumption change
- no backend schema or contract rename/remove
- behavior becomes stricter only when backend contract already says readonly/restricted

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-195.yaml`

## Next Suggestion

- continue with a second contract-parity batch on `ContractFormPage` or `ActionView`, focusing on block/section visibility and action-level disabled reasons from scene contract
