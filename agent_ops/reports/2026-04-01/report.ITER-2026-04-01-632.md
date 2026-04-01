# ITER-2026-04-01-632

- status: PASS
- mode: implement
- layer_target: Backend Semantic Layer
- module: execution advance blocked/error semantic continuity
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- in `project.execution.advance` added additive lifecycle semantic helper:
  - `_build_lifecycle_hints(project_id, reason_code)`
- attached `lifecycle_hints` to all blocked/error responses:
  - `PROJECT_CONTEXT_MISSING` (`ok=false`)
  - `PROJECT_NOT_FOUND` and all `result=blocked` branches (`ok=true`)
- kept execution state machine, task transition, and success path unchanged

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-632.yaml`: PASS

## Next Iteration Suggestion

- verify acceptance baseline and continue screening remaining write-intent handlers for semantic continuity consistency
