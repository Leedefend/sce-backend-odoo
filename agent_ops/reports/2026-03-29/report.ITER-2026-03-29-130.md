# Iteration Report: ITER-2026-03-29-130

- task: `agent_ops/tasks/ITER-2026-03-29-130.yaml`
- title: `Count searchpanel semantics in scene dsl surface profile`
- layer target: `backend orchestration`
- module: `smart_core scene_dsl_compiler`
- reason: `Scene dsl compiler still reports search usage with a legacy surface profile that ignores faceted searchpanel semantics. This iteration makes compile metadata consistent with the parser-driven search contract.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-130.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene dsl compiler surface profile count searchpanel semantics alongside filters and group_by.

## User Visible Outcome

- scene compile metadata now reflects faceted search usage instead of undercounting search semantics

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-130.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_dsl_compiler.py addons/smart_core/tests/test_scene_dsl_compiler_surface_profile.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_dsl_compiler_surface_profile.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `120`
- removed_lines: `0`

## Changed Files

- `addons/smart_core/core/scene_dsl_compiler.py`
- `addons/smart_core/tests/test_scene_dsl_compiler_surface_profile.py`
- `agent_ops/tasks/ITER-2026-03-29-130.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
