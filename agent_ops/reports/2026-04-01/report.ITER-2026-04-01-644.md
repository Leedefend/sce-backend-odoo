# ITER-2026-04-01-644

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: project entry context resolve guidance enrichment
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- in `ProjectEntryContextService` added `_build_lifecycle_guidance(...)`
- `resolve(...)` now returns additive fields:
  - `suggested_action`
  - `lifecycle_hints`
- semantics by availability:
  - `available=true`: guide to `project.dashboard.enter`
  - `available=false`: guide to `project.initiation.enter`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-644.yaml`: PASS

## Next Iteration Suggestion

- verify acceptance chain and continue business-fact usability screens
