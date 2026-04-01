# ITER-2026-04-01-621

- status: PASS
- mode: screen
- layer_target: Backend Semantic Layer
- module: lifecycle_hints coverage screen
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Decision

- PASS
- next backend family: `extend lifecycle_hints to non-base-orchestrator scene entry handlers`
- immediate candidate focus: `project_plan_bootstrap.enter` and `settlement.enter` entry responses

## Reason

- `lifecycle_hints` currently appears in base orchestrator responses and `project.initiation.enter`
- direct entry handlers outside base orchestrator path are likely to remain uncovered
- completing this coverage keeps frontend generic and removes pressure for view-side exceptions

## Next Iteration Suggestion

- open bounded backend implement batch for lifecycle_hints coverage in remaining entry handlers
