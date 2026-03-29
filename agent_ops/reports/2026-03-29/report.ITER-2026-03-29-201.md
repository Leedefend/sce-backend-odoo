## Summary

- created a dedicated live contract audit batch for project form completeness
- added `project_form_live_contract_audit.py` to verify the runtime `ui.contract` payload instead of relying only on a stored snapshot
- confirmed the live `project.project` form contract still lacks effective `views.form.field_modifiers`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-201.yaml`
- `agent_ops/scripts/project_form_live_contract_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-201.yaml`
- `python3 agent_ops/scripts/frontend_contract_parity_audit.py --snapshot docs/contract/snapshots/project_form_pm.json --frontend-file frontend/apps/web/src/pages/ContractFormPage.vue --expect-status PASS`
- `python3 -m py_compile agent_ops/scripts/project_form_live_contract_audit.py`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/project_form_live_contract_audit.py --db sc_demo --login sc_fx_pm --password prod_like --expect-field-modifiers missing'`

## Risk

- low risk audit-only batch
- no frontend or backend business code changed
- live verdict now depends on a repeatable local audit script instead of manual browser inspection

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-201.yaml`

## Next Suggestion

- open the next backend implementation batch to add real `views.form.field_modifiers` parsing/projection for `project.project` form contracts, then re-run the parity audit and a frontend visual check
