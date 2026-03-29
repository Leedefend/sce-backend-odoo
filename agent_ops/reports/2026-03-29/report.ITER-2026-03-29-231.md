## Summary

- fixed the actual backend form-contract gap in [contract_mixin.py](/mnt/e/sc-backend-odoo/addons/smart_core/app_config_engine/models/contract_mixin.py)
- corrected the native-gap audit traversal in [project_form_native_gap_audit.py](/mnt/e/sc-backend-odoo/agent_ops/scripts/project_form_native_gap_audit.py) so `tabs/pages` are counted instead of being misread as missing
- added regression coverage in [test_app_view_config_form_structure.py](/mnt/e/sc-backend-odoo/addons/smart_core/tests/test_app_view_config_form_structure.py)

## Key Outcome

- native-vs-parser audit now shows `gap_count=0`
- the earlier `page/group` parser gap was an audit traversal artifact; parser-native layout already preserved `notebook/page/group`
- the real backend product gap was governed form projection dropping:
  - `header_buttons`
  - `button_box`
  - `stat_buttons`
- that gap is now closed by preserving those subtrees in governed sanitize

## Changed Files

- `agent_ops/tasks/ITER-2026-03-29-231.yaml`
- `addons/smart_core/app_config_engine/models/contract_mixin.py`
- `addons/smart_core/tests/test_app_view_config_form_structure.py`
- `agent_ops/scripts/project_form_native_gap_audit.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-231.yaml`
- `python3 -m py_compile addons/smart_core/app_config_engine/models/contract_mixin.py addons/smart_core/tests/test_app_view_config_form_structure.py agent_ops/scripts/project_form_native_gap_audit.py`
- `python3 addons/smart_core/tests/test_app_view_config_form_structure.py`
- `python3 agent_ops/scripts/project_form_native_gap_audit.py --db sc_demo --login sc_fx_pm --container sc-backend-odoo-dev-odoo-1`

## Risk

- low-to-medium risk backend fix
- sanitize whitelist widened only for form structural/action subtrees already present in parser-native output
- no schema, ACL, record-rule, or business fact semantics changed

## Rollback

- run the `git restore ...` command listed in `agent_ops/tasks/ITER-2026-03-29-231.yaml`

## Next Suggestion

- return to frontend detail rendering with the corrected assumption:
  - backend parser/projection now preserves native form structure and actions
  - the next remaining gaps should be treated as frontend consumption/rendering gaps, not parser completeness gaps
