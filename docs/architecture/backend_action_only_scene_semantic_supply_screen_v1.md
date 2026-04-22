# Backend Action-Only Scene Semantic Supply Screen v1

## Goal

Decide the backend change layer and bounded semantic-supply direction for
action-only entries that still do not emit enough scene identity for frontend
route convergence.

This screen does not implement backend changes. It decides the next legal
backend batch.

## Fixed Architecture Declaration

- Layer Target: Backend semantic-supply screen
- Module: action-only scene identity supply
- Module Ownership: scene entry orchestration contract
- Kernel or Scenario: scenario
- Reason: frontend route convergence has been reduced to the point where the
  remaining residual gap is action-only entry with missing scene identity

## Backend Sub-Layer Decision

### Decision

The next change belongs to the `scene-orchestration layer`.

### Why not business-fact layer

- the missing data is not a new business truth such as ownership, amount,
  workflow state, or permission fact
- the missing data is a consumption-ready semantic organization: which scene
  identity an action-only entry should expose so the frontend can remain a
  generic scene consumer

### Why scene-orchestration layer fits

- the frontend already knows how to consume scene identity when the backend
  emits it
- the remaining gap appears when action/menu entry still arrives without a
  scene-oriented envelope
- supplying `scene_key` or equivalent scene identity is orchestration semantics,
  not a new business fact

## Screen Conclusion

The remaining route-convergence gap should be handled by backend scene
orchestration, not by more frontend special-casing.

The backend objective is:

- for action-only entries that are intended to map to a scene, emit scene
  identity directly in the orchestrated contract so frontend entry no longer
  has to infer it from native action/menu facts

## Bounded Next-Step Direction

The next backend implementation batch should answer, in a bounded scope:

1. where the action-only entry contract is assembled today
2. which orchestrated envelope can carry `scene_key` or equivalent scene target
3. how to emit that identity without reintroducing native menu/action structures
   as frontend authority

## Guardrail

The next backend batch must not:

- fabricate scene identity where backend has no legitimate orchestration mapping
- modify business facts to patch route semantics
- re-open native menu/action raw contracts as the primary frontend entry source
