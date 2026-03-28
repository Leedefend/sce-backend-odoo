# Iteration Report: ITER-2026-03-29-142

- task: `agent_ops/tasks/ITER-2026-03-29-142.yaml`
- title: `Count canonical action semantics in scene ready metrics`
- layer target: `backend orchestration`
- module: `smart_core scene_ready_contract_builder`
- reason: `Scene ready action surfaces are already canonicalized around primary_actions, groups and selection_mode, but consumption metrics still only count action_surface when counts.total exists. This iteration aligns metrics with the canonical action surface shape.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-142.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene ready consumption metrics count canonical action_surface semantics even when counts have not been materialized yet.

## User Visible Outcome

- scenes with primary_actions or grouped actions are no longer undercounted as missing action consumption

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-142.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_ready_consumption_metrics.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `88`
- removed_lines: `1`

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `agent_ops/tasks/ITER-2026-03-29-142.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
