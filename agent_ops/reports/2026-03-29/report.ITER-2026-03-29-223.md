## Summary

- tightened `ContractFormPage` so record-detail routes with usable live form facts prefer a native-first form surface instead of stacking generic platform helper blocks ahead of the layout
- suppressed overview, warning, strict-contract, workflow, search-filter, and body-action sections when the page is already backed by a usable form contract
- reduced section-shell noise for native detail routes by dropping field-count summaries and generic eyebrow labels unless the section kind carries real structure

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-223.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-223.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low-risk frontend detail-shell batch
- kept generic to record-detail routes; `project.project` remains only the first validation sample
- no backend, schema, ACL, or record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-223.yaml`

## Next Suggestion

- refresh the project detail page and verify the page now leads with statusbar, contract actions, and sectioned form fields; then continue with kanban parity using the same fact-first native-first strategy
