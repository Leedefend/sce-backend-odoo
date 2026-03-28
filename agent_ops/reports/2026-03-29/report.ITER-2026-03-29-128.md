# Iteration Report: ITER-2026-03-29-128

- task: `agent_ops/tasks/ITER-2026-03-29-128.yaml`
- title: `Count faceted searchpanel surfaces in scene ready metrics`
- layer target: `backend orchestration`
- module: `smart_core scene_ready_contract_builder`
- reason: `Scene ready metrics still count search usage with a legacy predicate that ignores searchpanel-only faceted surfaces. This iteration makes semantic search metrics consistent with the parser-driven contract.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-128.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene ready consumption metrics treat searchpanel-only search surfaces as valid semantic search usage.

## User Visible Outcome

- scene ready metrics no longer undercount faceted search scenes that only expose searchpanel semantics

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-128.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_ready_consumption_metrics.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `148`
- removed_lines: `1`

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `agent_ops/tasks/ITER-2026-03-29-128.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
