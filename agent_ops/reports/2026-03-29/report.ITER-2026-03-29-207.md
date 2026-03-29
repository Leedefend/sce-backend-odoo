## Summary

- added a dedicated live parity audit for `project.project` form button sources
- confirmed the current project form button noise is not caused by `toolbar.header/sidebar/footer` merges
- live contract currently exposes exactly `3` form buttons, all of which project into frontend header-like actions
- one live button key is suspicious for an existing project detail page: `obj_action_view_tasks_Create project`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-207.yaml`
- `agent_ops/scripts/project_form_button_parity_audit.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-207.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_button_parity_audit.py`
- `bash -lc 'export E2E_BASE_URL=http://127.0.0.1:8070; python3 agent_ops/scripts/project_form_button_parity_audit.py --db sc_demo --login sc_fx_pm --password prod_like --expect-status PASS'`

## Risk

- low risk audit-only batch
- no frontend page code or backend business behavior changed
- provides a repeatable fact base for the next backend button-source diagnosis batch

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-207.yaml`

## Next Suggestion

- open the next full-chain diagnosis batch on backend project form button facts, trace where `obj_action_view_tasks_Create project` enters the governed form contract, and determine whether the source is parser semantics, raw Odoo view buttons, or contract projection
