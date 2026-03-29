## Summary

- extracted the full source rows for the suspicious project-form button family
- confirmed parser-level fact is a simple smart/stat button: `action_view_tasks` with label `任务`
- confirmed dispatcher-level normalization explodes that single source into multiple divergent rows, including:
  - `obj_action_view_tasks_Create project`
  - `obj_action_view_tasks_View Tasks`
  - `obj_action_view_tasks`
  - `obj_action_view_tasks_任务`
- confirmed the suspicious `Create project` row is not backed by a resolved `ir.actions.*` reference; it is an object-method row carrying `method=action_view_tasks`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-210.yaml`
- `agent_ops/scripts/project_form_suspicious_button_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-210.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_suspicious_button_audit.py`
- `python3 agent_ops/scripts/project_form_suspicious_button_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Risk

- low risk audit-only batch
- no frontend or backend production code changed
- narrows the next implementation batch to dispatcher/source action normalization rather than parser extraction or frontend rendering

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-210.yaml`

## Next Suggestion

- open the next backend implementation batch to stop dispatcher/action normalization from duplicating `action_view_tasks` into multiple mislabeled rows, or add project-form-specific dedup/filter logic before governance curation
