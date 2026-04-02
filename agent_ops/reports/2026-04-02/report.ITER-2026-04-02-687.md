# ITER-2026-04-02-687

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: execution-advance context-missing continuity
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- in `project.execution.advance` context-missing branch added additive:
  - `data.suggested_action_payload.intent = "project.initiation.enter"`
  - `data.suggested_action_payload.reason_code = "PROJECT_CONTEXT_MISSING"`
  - `data.suggested_action_payload.params.reason_code = "PROJECT_CONTEXT_MISSING"`
- preserved existing `error` and `lifecycle_hints` behavior

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-02-687.yaml`: PASS

## Next Iteration Suggestion

- run acceptance verification and continue next bounded screen batch
