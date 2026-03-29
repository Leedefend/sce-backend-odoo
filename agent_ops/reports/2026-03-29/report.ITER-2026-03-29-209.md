## Summary

- added a dedicated governance-path audit for `project.project` form buttons
- confirmed the suspicious `Create project` button is already present in dispatcher output
- confirmed `finalize_contract` reduces button count but still keeps the suspicious button
- confirmed `apply_contract_governance` trims project form actions from `17` to `3`, but still preserves `obj_action_view_tasks_Create project`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-209.yaml`
- `agent_ops/scripts/project_form_button_governance_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-209.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_button_governance_audit.py`
- `python3 agent_ops/scripts/project_form_button_governance_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Risk

- low risk audit-only batch
- no frontend or backend production code changed
- narrows the next fix batch to button-source cleanup and/or project-form governance filtering

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-209.yaml`

## Next Suggestion

- open the next backend implementation batch to remove or filter the dispatcher-level noisy project form actions, with special focus on `obj_action_view_tasks_Create project` and other mislabeled project-form actions that survive current governance
