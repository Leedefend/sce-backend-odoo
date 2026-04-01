# ITER-2026-04-01-637

- status: PASS
- mode: screen
- layer_target: Backend Semantic Layer
- module: project enter error fallback semantic screen
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Screen Result

- both handlers currently do:
  - read `lifecycle_hints = dict((data or {}).get("lifecycle_hints") or {})`
  - return `PROJECT_NOT_FOUND` with that value
- when upstream data lacks hints, returned lifecycle guidance can become empty
- selected next bounded candidate family:
  - add non-empty fallback lifecycle_hints builder for `PROJECT_NOT_FOUND` in
    `project.dashboard.enter` and `project.execution.enter`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-637.yaml`: PASS

## Next Iteration Suggestion

- open implement + verify batch for error fallback lifecycle_hints in dashboard/execution enter handlers
