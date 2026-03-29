## Summary

- switched form-page action filtering to parsed form button facts from `app.view.config.arch_parsed`
- stopped relying on governed `views.form` button buckets, which the live audit proved are empty
- extended the live project-form button audit to fail if the misleading `Create project` label still appears

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-214.yaml`
- `addons/smart_core/app_config_engine/services/assemblers/page_assembler.py`
- `addons/smart_core/tests/test_page_assembler_form_actions.py`
- `agent_ops/scripts/project_form_button_parity_audit.py`
- `agent_ops/scripts/project_form_button_live_label_probe.py`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-214.yaml`
- `python3 -m py_compile addons/smart_core/app_config_engine/services/assemblers/page_assembler.py addons/smart_core/tests/test_page_assembler_form_actions.py agent_ops/scripts/project_form_button_parity_audit.py agent_ops/scripts/project_form_button_live_label_probe.py`
- `python3 addons/smart_core/tests/test_page_assembler_form_actions.py`
- `make restart`
- `python3 agent_ops/scripts/project_form_button_live_label_probe.py --db sc_demo --login sc_fx_pm --password prod_like --container sc-backend-odoo-dev-odoo-1 --forbid-label "Create project"`

## Risk

- low-risk backend batch
- scoped to form action sourcing only
- no schema/ACL/record-rule changes

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-214.yaml`

## Next Suggestion

- if live verification passes, verify the project detail page in the frontend and then reduce remaining button-count/ordering differences
