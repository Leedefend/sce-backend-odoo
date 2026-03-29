## Summary

- polished the generic detail-shell presentation so the existing `detail shell -> grouped sections -> fields` hierarchy reads more clearly in the page body
- strengthened the outer detail container and softened nested group cards, making grouped sections feel embedded within the primary form body
- kept the batch presentation-only and generic to all record-detail routes using the shared `ContractFormPage`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-225.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-225.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend presentation batch
- scoped to visual hierarchy polish only
- no backend, contract, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-225.yaml`

## Next Suggestion

- refresh the project detail page and verify the body hierarchy now reads more clearly; then continue with notebook/page-to-tabs support when a live form sample exposes those containers
