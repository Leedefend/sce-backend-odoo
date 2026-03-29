## Summary

- implemented `section_shells` in `ContractFormPage`
- wrapped form sections with local section shell containers
- projected section shell metadata (`shellClass`, `eyebrow`, `summary`) from existing layout sections
- closed the current frontend parity audit gap for project form

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-200.yaml`
- `frontend/apps/web/src/pages/ContractFormPage.vue`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-200.yaml`
- `python3 agent_ops/scripts/frontend_contract_parity_audit.py --snapshot docs/contract/snapshots/project_form_pm.json --frontend-file frontend/apps/web/src/pages/ContractFormPage.vue --expect-status PASS`
- `bash -lc 'source ~/.nvm/nvm.sh >/dev/null 2>&1 && nvm use 20 >/dev/null && pnpm -C frontend/apps/web typecheck:strict'`

## Risk

- low risk frontend-only page shell refinement
- no backend contract change
- no form submission logic change

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-200.yaml`

## Next Suggestion

- move to the remaining audited gap: verify live backend completeness for `views.form.field_modifiers`, then patch backend if runtime confirms the sample gap is real
