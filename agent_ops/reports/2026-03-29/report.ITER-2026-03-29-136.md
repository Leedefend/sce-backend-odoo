# Iteration Report: ITER-2026-03-29-136

- task: `agent_ops/tasks/ITER-2026-03-29-136.yaml`
- title: `Preserve search mode in scene dsl compile fallback`
- layer target: `backend orchestration`
- module: `smart_core scene_dsl_compiler`
- reason: `Scene dsl compiler already preserves fields, filters, group_by and searchpanel from canonical ui base search facts, but still drops search mode. This iteration keeps faceted/filter_bar semantics at compile time.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-136.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene dsl compiler preserve canonical search_surface.mode from ui base search facts during early surface fallback.

## User Visible Outcome

- compiled scene contracts retain faceted/filter_bar search mode before later scene-ready bridges run

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-136.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py addons/smart_core/tests/test_scene_dsl_compiler_search_mode_fallback.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_dsl_compiler_search_mode_fallback.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `120`
- removed_lines: `0`

## Changed Files

- `addons/smart_core/core/scene_dsl_compiler.py`
- `addons/smart_core/tests/test_scene_dsl_compiler_search_mode_fallback.py`
- `agent_ops/tasks/ITER-2026-03-29-136.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
