# Iteration Report: ITER-2026-03-29-141

- task: `agent_ops/tasks/ITER-2026-03-29-141.yaml`
- title: `Count compile-level search semantics in scene ready metrics`
- layer target: `backend orchestration`
- module: `smart_core scene_ready_contract_builder`
- reason: `Scene ready normalization already keeps search_surface.default_sort and search_surface.mode, but consumption metrics still undercount search semantics by only checking filters, fields, group_by and searchpanel. This iteration aligns metrics with the canonical search surface.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-141.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene ready consumption metrics count canonical search mode and default sort as valid search-surface consumption.

## User Visible Outcome

- faceted-only or default-sort-only scenes are no longer undercounted as missing search consumption in scene-ready metrics

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-141.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_ready_contract_builder.py addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_ready_consumption_metrics.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `81`
- removed_lines: `0`

## Changed Files

- `addons/smart_core/core/scene_ready_contract_builder.py`
- `addons/smart_core/tests/test_scene_ready_consumption_metrics.py`
- `agent_ops/tasks/ITER-2026-03-29-141.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
