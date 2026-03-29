## Summary

- added a native-vs-parser audit script for `project.project` form in [project_form_native_gap_audit.py](/mnt/e/sc-backend-odoo/agent_ops/scripts/project_form_native_gap_audit.py)
- compared three backend fact layers directly:
  - native Odoo form XML from `_safe_get_view_data()`
  - parser output from `app.view.parser.parse_odoo_view()`
  - internal governed form block from `app.view.config.get_contract_api()`
- current native truth shows the backend still has structural parsing/projection gaps:
  - native has `1` notebook and `3` pages, but parser/internal contract only preserve `notebook`, not `page`
  - native has `11` groups, parser/internal contract only preserve `3`
  - native header buttons exist in XML and parser output, but are dropped by the internal contract block
  - native button box exists in XML and parser output, but is dropped by the internal contract block

## Key Findings

- this is not primarily a frontend-consumer problem; backend structural facts are already reduced before the frontend sees them
- parser is partially correct:
  - `statusbar_field=lifecycle_state` is preserved
  - `header_buttons` are preserved
  - `button_box/stat_buttons` are preserved
  - `field_modifiers=47` are preserved
- parser still has layout loss against native XML:
  - native `page_count=3` vs parser `page=0`
  - native `group_count=11` vs parser `group=3`
- internal contract projection loses more structure:
  - `header_buttons_count=0`
  - `button_box_count=0`
  - `page=0`
  - `group=3`

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-230.yaml`
- `agent_ops/scripts/project_form_native_gap_audit.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-230.yaml`
- `python3 -m py_compile agent_ops/scripts/project_form_native_gap_audit.py`
- `python3 agent_ops/scripts/project_form_native_gap_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Risk

- low-risk audit batch
- no frontend or backend product code changed
- live comparison used the real Odoo container, so the gap list is based on runtime facts instead of stale snapshots

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-230.yaml`

## Next Suggestion

- open a backend parser/projection batch first, not a frontend layout batch
- priority order:
  - preserve native `page` containers in parser layout
  - preserve deeper `group` structure in parser layout
  - stop dropping `header_buttons` / `button_box` in the internal governed form contract
