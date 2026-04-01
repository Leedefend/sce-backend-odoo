# ITER-2026-04-01-532

- status: PASS
- mode: screen
- layer_target: Frontend Layer
- module: native metadata list toolbar screen
- risk: low

## Screen Result

- next_candidate_family: `count parity gap`
- family_scope: `frontend/apps/web/src/components/page/PageToolbar.vue` optimized secondary metadata section
- reason: `count parity gap` is the cleanest next slice because it stays inside one display-only component, restores parity with the existing non-optimized toolbar wording, and does not reinterpret route, sort, or filter semantics.

## Deferred Families

- `default sort appears as an active condition`: still valid, but it changes the semantics of what counts as an active condition and is slightly more interpretation-heavy
- `toggle count mixes actionable and static items`: valid but coupled to advanced-filter IA wording, so it is broader than the count-parity fix
- `route preset provenance label`: valid but needs product wording judgment about when source should stay visible

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-532.yaml`: PASS

## Next Iteration Suggestion

- open a low-risk implementation batch that restores explicit metadata counts in the optimized toolbar without changing filter behavior
