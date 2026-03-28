# Iteration Report: ITER-2026-03-29-143

- task: `agent_ops/tasks/ITER-2026-03-29-143.yaml`
- title: `Normalize rich base fact metrics in scene ready`
- layer target: `backend orchestration`
- module: `smart_core scene_ready_contract_builder`
- reason: `Scene ready metrics currently use bare truthiness for base_facts, which overcounts richer fact objects like {"available": false}. This iteration normalizes hit detection while staying within the same metrics subsystem.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-143.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene ready consumption metrics correctly interpret richer base_fact objects instead of treating any non-empty dict as a hit.

## User Visible Outcome

- diagnostics and governance metrics no longer overcount unavailable search/action facts when richer fact objects are present

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-143.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_ready_consumption_metrics.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `91`
- removed_lines: `1`

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `agent_ops/tasks/ITER-2026-03-29-143.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
