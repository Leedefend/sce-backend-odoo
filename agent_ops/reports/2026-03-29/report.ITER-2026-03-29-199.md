## Summary

- added a project-form contract parity audit script
- audited backend snapshot `project_form_pm.json` against frontend consumer `ContractFormPage.vue`
- produced a first explicit gap matrix for the new productization line

## Findings

- backend present: `head.access_policy`, `views.form.layout`, `views.form.statusbar.field`, `buttons`, `permissions.effective.rights`, `permissions.field_groups`, `field_policies`, `field_semantics`, `visible_fields`, `workflow`, `validator`
- backend missing in the current audit sample: `views.form.field_modifiers`
- frontend already covers: title identity, runtime permissions, statusbar strip, top action strip, layout walk, section mapping, readonly projection
- frontend uncovered in the current clean baseline: `section_shells`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-199.yaml`
- `agent_ops/scripts/frontend_contract_parity_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-199.yaml`
- `python3 -m py_compile agent_ops/scripts/frontend_contract_parity_audit.py`
- `python3 agent_ops/scripts/frontend_contract_parity_audit.py --snapshot docs/contract/snapshots/project_form_pm.json --frontend-file frontend/apps/web/src/pages/ContractFormPage.vue --expect-status PASS`

## Risk

- low risk governance-only addition
- no frontend runtime behavior change
- no backend contract change

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-199.yaml`

## Next Suggestion

- open the next implementation batch directly against the current matrix:
  1. frontend `section_shells`
  2. then backend `views.form.field_modifiers` completeness if real runtime also lacks it
