## Summary

- made `ContractFormPage` prefer live contract buttons over `sceneReady` action overlays for `project.project` detail forms
- hid duplicated workflow transition chips, search filters, and body action sections on project detail pages
- kept non-project and create-profile paths unchanged so the reduction stays scoped to the noisy detail-form case

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-215.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-215.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend consumer batch
- scoped to project detail form action rendering only
- no backend, schema, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-215.yaml`

## Next Suggestion

- refresh the project detail page and verify the visible action count now matches the cleaned live backend contract more closely; then trim any remaining header ordering or label mismatches
