# ITER-2026-04-02-711

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance explicit task targeting
- priority_lane: P1_explicit_task_targeting
- risk: low

## Summary of Change

- added explicit task selector:
  - supports `task_id` from `params` or `ctx`
  - if absent, keeps prior auto-selection behavior
- upgraded task transition helpers to return telemetry:
  - `task_id`
  - `task_state_before`
  - `task_state_after`
- atomic transition path now carries task telemetry into:
  - blocked responses from atomic rollback
  - success response after transition
- added targeted reason:
  - `EXECUTION_TASK_TARGET_INVALID` for explicit but invalid/unusable target

## Verification Result

- `python3 -m py_compile addons/smart_construction_core/handlers/project_execution_advance.py`: PASS
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-711.yaml`: PASS

## Next Iteration Suggestion

- run acceptance verification and then move to P2 logging tightening
