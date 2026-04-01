# ITER-2026-04-01-535

- status: PASS
- mode: screen
- layer_target: Frontend Layer
- module: native metadata list toolbar screen
- risk: low

## Screen Result

- next_candidate_family: `default sort appears as an active condition`
- family_scope: `frontend/apps/web/src/components/page/PageToolbar.vue` active condition summary
- reason: `当前条件` should communicate user-applied state, but the current summary always includes the sort chip whenever a sort label exists. Hiding the native default sort from that summary is a small display-semantics fix inside one component and does not require new data sources.

## Deferred Families

- `advanced filters toggle count mixes actionable and static items`: still valid, but broader because it changes fold-state affordance wording
- `route preset provenance label`: still valid, but needs product wording judgment on source visibility

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-535.yaml`: PASS

## Next Iteration Suggestion

- open a low-risk implementation batch that hides native default sort from `当前条件` while preserving non-default sort visibility
