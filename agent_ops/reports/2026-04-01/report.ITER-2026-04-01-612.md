# ITER-2026-04-01-612

- status: PASS
- mode: screen
- layer_target: Frontend Layer
- module: lifecycle usability architecture correction screen
- priority_lane: P1_project_lifecycle_usability
- risk: low

## Decision

- PASS
- selected correction slice: `replace frontend model branching with semantic-driven copy`
- enforce boundary: frontend consumes generic semantics only

## Reason

- user explicitly rejected frontend model-specific branching
- current lifecycle hints can be preserved by consuming `primaryActionLabel`
- this keeps usability gains without breaking architecture boundary

## Next Iteration Suggestion

- implement semantic-driven empty/list hint copy in `useStatus.ts` and `ListPage.vue`
- open a dedicated backend semantic-gap batch next to provide richer scene-level guidance fields
