## Summary

- fixed governed form contract sanitization so `field_modifiers` is preserved
- added subtree passthrough for `field_modifiers`, preventing field-name entries from being pruned during recursive sanitize
- verified that live `project.project` form `ui.contract` now exposes effective `views.form.field_modifiers`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-204.yaml`
- `addons/smart_core/app_config_engine/models/contract_mixin.py`
- `addons/smart_core/tests/test_contract_mixin_governed_form.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-204.yaml`
- `python3 -m py_compile addons/smart_core/app_config_engine/models/contract_mixin.py addons/smart_core/tests/test_contract_mixin_governed_form.py`
- `python3 addons/smart_core/tests/test_contract_mixin_governed_form.py`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/project_form_live_contract_audit.py --db sc_demo --login sc_fx_pm --password prod_like --expect-field-modifiers present'`

## Risk

- low risk backend projection fix
- no public intent rename
- no schema change, only restoration of already-parsed form metadata into governed contract output

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-204.yaml`

## Next Suggestion

- return to the frontend project form page and wire field-level readonly/required/invisible behavior from `views.form.field_modifiers`, then validate against the real page visually
