# Iteration Report: ITER-2026-03-29-132

- task: `agent_ops/tasks/ITER-2026-03-29-132.yaml`
- title: `Preserve search mode in ui base search facts`
- layer target: `backend orchestration`
- module: `smart_core ui_base_contract_adapter`
- reason: `Ui base contract adapter still emits a search_fact subset that drops canonical search mode, so faceted/filter_bar semantics are not fully represented at the adapter entry.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-132.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make ui base contract adapter preserve canonical search mode in search_fact instead of only exposing structural search lists.

## User Visible Outcome

- orchestrator_input.search_fact now keeps faceted/filter_bar mode when canonical search semantics provide it

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-132.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/ui_base_contract_adapter.py addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `PASS` `python3 addons/smart_core/tests/test_ui_base_contract_adapter.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `113`
- removed_lines: `1`

## Changed Files

- `addons/smart_core/core/ui_base_contract_adapter.py`
- `addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `agent_ops/tasks/ITER-2026-03-29-132.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
