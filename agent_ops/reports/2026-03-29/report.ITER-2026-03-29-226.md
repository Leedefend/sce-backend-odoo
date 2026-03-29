## Summary

- aligned the generic detail top area into a single command bar so status progression and contract actions now read as one native-first interaction surface
- kept the implementation generic inside `ContractFormPage` without adding any model-specific command bar logic
- improved visible detail-page structure while preserving the same backend fact inputs

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-226.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-226.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend detail-surface batch
- scoped to command-bar presentation only
- no backend, contract, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-226.yaml`

## Next Suggestion

- refresh the project detail page and verify the top area now reads as a single command band; then continue with list/detail interaction parity or notebook/page tabs when a live sample is available
