## Summary

- added a dedicated backend source-path audit for `project.project` form buttons
- confirmed the suspicious project-form button does not come from frontend-only merging
- confirmed parser-level form button extraction is non-empty, while `app.view.config.get_contract_api(...)` is empty
- therefore the live `ui.contract` button facts must be reintroduced after `get_contract_api`, most likely in the handler/governance delivery path

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-208.yaml`
- `agent_ops/scripts/project_form_button_source_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-208.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_button_source_audit.py`
- `python3 agent_ops/scripts/project_form_button_source_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Risk

- low risk audit-only batch
- no frontend or backend production code changed
- narrows the next implementation batch to the `ui.contract` delivery chain instead of parser or frontend presentation

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-208.yaml`

## Next Suggestion

- open the next backend diagnosis batch on the `ui.contract` delivery path, specifically compare `load_contract.py` / governance output against `get_contract_api(...)` to find where the three live project form buttons are injected and why one becomes `Create project`
