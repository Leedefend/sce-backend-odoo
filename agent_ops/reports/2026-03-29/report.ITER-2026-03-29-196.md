## Summary

- projected project form status semantics into a visible statusbar strip
- added a contract-driven top action strip for project form header actions
- added a page overview strip to make the form page feel like a business page instead of a generic field container
- improved project form page identity with project-aware title/subtitle handling

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-196.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-196.yaml`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && python3 agent_ops/scripts/frontend_verify_gate.py --frontend-dir frontend/apps/web --expect-status PASS'`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk frontend-only page shell enhancement
- no backend contract or business rule changes
- skeleton parity uses existing contract fields/buttons/statusbar rather than frontend inference

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-196.yaml`

## Next Suggestion

- continue project form parity by projecting more layout containers from `views.form.layout` into richer section shells and by exposing relation degradation hints more explicitly
