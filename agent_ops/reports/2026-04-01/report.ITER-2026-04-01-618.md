# ITER-2026-04-01-618

- status: PASS
- mode: screen
- layer_target: Backend Semantic Layer
- module: project lifecycle semantic supply screen
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Decision

- PASS
- next backend candidate family: `lifecycle_hints semantic contract on scene entry payload`
- frontend should consume backend-provided lifecycle guidance, not infer by model

## Reason

- `project.initiation.enter` and scene entry orchestrators expose `suggested_action`, but payload lacks stable UI guidance fields such as action label/hint group/entry-step semantics
- `BaseSceneEntryOrchestrator` currently emits `suggested_action` with key/intent/params/reason only; no explicit user-facing lifecycle guidance envelope
- without explicit semantic hints, frontend is pressured to infer model-specific copy and flow cues

## Next Iteration Suggestion

- open bounded backend implement batch to add a generic `lifecycle_hints` payload (for example create/manage/next-step labels and reason semantics) in scene entry responses
