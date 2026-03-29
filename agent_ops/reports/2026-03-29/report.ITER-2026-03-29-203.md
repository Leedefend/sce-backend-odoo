## Summary

- created a container-internal parser path audit for `project.project` form
- confirmed the live parser does produce `field_modifiers`
- confirmed `arch_parsed` also stores those `field_modifiers`
- isolated the actual drop point to the final contract projection path (`arch_parsed -> get_contract_api().views.form.field_modifiers`)

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-203.yaml`
- `agent_ops/scripts/project_form_parser_path_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-203.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_parser_path_audit.py`
- `python3 agent_ops/scripts/project_form_parser_path_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Root Cause Verdict

- `fields_view_get` raw field metadata contributes `0` field modifiers
- primary parser output contains `47` field modifiers
- `app.view.config.arch_parsed` contains the same `47` field modifiers
- final `ui.contract` form block exposes `0` field modifiers

Therefore the missing link is not parser completeness anymore. The loss happens after parsing, when final form contract data is projected from stored `arch_parsed`.

## Risk

- low risk audit-only batch
- no frontend or backend product logic changed
- next implementation batch can now target a single projection stage instead of changing parser behavior again

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-203.yaml`

## Next Suggestion

- open the next backend implementation batch on `app.view.config.get_contract_api()` / final form contract projection and restore `field_modifiers` from `arch_parsed` when the projected form block drops them
