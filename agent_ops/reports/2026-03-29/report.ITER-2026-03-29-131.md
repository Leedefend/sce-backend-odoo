# Iteration Report: ITER-2026-03-29-131

- task: `agent_ops/tasks/ITER-2026-03-29-131.yaml`
- title: `Preserve searchpanel in ui base search facts`
- layer target: `backend orchestration`
- module: `smart_core ui_base_contract_adapter`
- reason: `Ui base contract adapter still emits a legacy search_fact subset that drops searchpanel semantics, so faceted search is not fully represented at the canonical adapter entry.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-131.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make ui base contract adapter preserve searchpanel semantics in canonical search facts instead of only exposing default_sort, filters, group_by, and fields.

## User Visible Outcome

- orchestrator_input.search_fact now includes searchpanel semantics for faceted search contracts

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-131.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/ui_base_contract_adapter.py addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `PASS` `python3 addons/smart_core/tests/test_ui_base_contract_adapter.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `113`
- removed_lines: `0`

## Changed Files

- `addons/smart_core/core/ui_base_contract_adapter.py`
- `addons/smart_core/tests/test_ui_base_contract_adapter.py`
- `agent_ops/tasks/ITER-2026-03-29-131.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
