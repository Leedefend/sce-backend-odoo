# ITER-2026-04-01-650

- status: PASS
- mode: implement
- layer_target: Backend Usability
- module: project entry context options guidance enrichment
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Summary of Change

- in `ProjectEntryContextService` added `_build_options_guidance(...)`
- `list_options(...)` now returns additive fields:
  - `suggested_action`
  - `lifecycle_hints`
- semantics:
  - options non-empty -> guide to `project.dashboard.enter` (active or first option)
  - options empty -> guide to `project.initiation.enter`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-650.yaml`: PASS

## Next Iteration Suggestion

- run acceptance verification and continue business-fact usability screen
