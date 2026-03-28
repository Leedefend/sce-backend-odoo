# Iteration Report: ITER-2026-03-28-017

- task: `agent_ops/tasks/ITER-2026-03-28-017.yaml`
- title: `Align system_init verify scripts with current login contract`
- layer target: `Verification Governance`
- module: `scripts/verify system_init live guards`
- reason: `Remove outdated login-contract assumptions from system_init live verifies so they test the runtime refactor rather than fail on unrelated auth response shape drift.`
- classification: `PASS`
- report source: `agent_ops/state/task_results/ITER-2026-03-28-017.json`
- validation passed: `True`
- verification passed: `True`

## Goal

Update system_init live verify scripts so they read the current login token contract and can validate the system_init refactor against the running environment.

## User Visible Outcome

- system_init verify scripts accept the current login response shape
- live system_init verifies can run against the local environment
- the first code batch can be revalidated instead of remaining blocked by outdated verification assumptions

## Verification

- `PASS` `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-28-017.yaml`
- `PASS` `python3 -m py_compile scripts/verify/system_init_snapshot_equivalence.py scripts/verify/system_init_runtime_context_stability.py`
- `PASS` `make verify.system_init.snapshot_equivalence`
- `PASS` `make verify.system_init.runtime_context.stability`

## Risk Scan

- risk_level: `medium`
- stop_required: `False`
- matched_rules: `sensitive_pattern`
- changed_files: `8`
- added_lines: `392`
- removed_lines: `123`

## Changed Files

- `addons/smart_core/core/system_init_scene_runtime_surface_builder.py`
- `addons/smart_core/core/system_init_scene_runtime_surface_context.py`
- `addons/smart_core/handlers/system_init.py`
- `agent_ops/tasks/ITER-2026-03-28-016.yaml`
- `agent_ops/tasks/ITER-2026-03-28-017.yaml`
- `agent_ops/tasks/ITER-2026-03-28-018.yaml`
- `scripts/verify/system_init_runtime_context_stability.py`
- `scripts/verify/system_init_snapshot_equivalence.py`

## Risk Evidence

- critical_hits: `0`
- high_risk_hits: `0`
- sensitive_pattern_hits: `fields\.`

## Conclusion

- classification: `PASS`
- reasons: `all_acceptance_passed, no_high_risk_change, user_visible_progress`
- triggered_stop_conditions: `none`
