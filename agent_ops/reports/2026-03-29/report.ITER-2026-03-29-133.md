# Iteration Report: ITER-2026-03-29-133

- task: `agent_ops/tasks/ITER-2026-03-29-133.yaml`
- title: `Normalize group_bys alias in ui base search facts`
- layer target: `backend orchestration`
- module: `smart_core ui_base_contract_adapter`
- reason: `Ui base contract adapter still expects canonical group_by only, while parser-aligned payloads often expose group_bys. This iteration normalizes the alias at the adapter entry.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-133.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make ui base contract adapter normalize parser-style group_bys into canonical search_fact.group_by.

## User Visible Outcome

- orchestrator_input.search_fact now preserves group-by semantics even when upstream payload still uses group_bys naming

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-133.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/ui_base_contract_adapter.py addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `PASS` `python3 addons/smart_core/tests/test_ui_base_contract_adapter.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `117`
- removed_lines: `2`

## Changed Files

- `addons/smart_core/core/ui_base_contract_adapter.py`
- `addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `agent_ops/tasks/ITER-2026-03-29-133.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
