# Iteration Report: ITER-2026-03-29-126

- task: `agent_ops/tasks/ITER-2026-03-29-126.yaml`
- title: `Make scene merge resolver preserve searchpanel semantics`
- layer target: `backend orchestration`
- module: `smart_core scene_merge_resolver`
- reason: `Scene merge resolver still treats searchpanel as a second-class field, so parser-derived faceted search semantics can be dropped during policy/provider merge. This iteration promotes searchpanel to a first-class merged search surface field.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-29-126.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Make scene policy/provider merge treat searchpanel as a first-class search surface field instead of only merging filters, group_by, and fields.

## User Visible Outcome

- released scene contracts now preserve parser-derived searchpanel semantics across policy and provider merge steps

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-29-126.yaml`
- `PASS` `python3 -m py_compile addons/smart_core/core/scene_merge_resolver.py addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py`
- `PASS` `python3 addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py`

## Risk Scan

- risk_level: `low`
- stop_required: `False`
- matched_rules: `none`
- changed_files: `3`
- added_lines: `135`
- removed_lines: `1`

## Changed Files

- `addons/smart_core/core/scene_merge_resolver.py`
- `addons/smart_core/tests/test_scene_merge_resolver_searchpanel_semantics.py`
- `agent_ops/tasks/ITER-2026-03-29-126.yaml`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
