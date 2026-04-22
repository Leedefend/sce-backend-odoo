# Menu Scene Resolve Host Timeout Repair L v1

## Goal

Repair the host menu-scene-resolve verifier so unreachable host proxy paths time
out quickly and fall back deterministically, instead of hanging for an
unbounded period.

## Scope

- `scripts/verify/fe_menu_scene_resolve_smoke.js`

## Fixed Architecture Declaration

- Layer Target: Verification surface repair
- Module: menu scene resolve host verifier
- Module Ownership: scripts/verify
- Kernel or Scenario: scenario
- Reason: after host fallback repair, the remaining issue is blackholed 8070
  connectivity that prevents the verifier from reaching its fallback in bounded
  time

## Implemented Changes

- request-level timeout handling is added to host verifier network calls
- the preferred `8070` path can now fail fast and fall back to `8069`
- business assertions and scene coverage logic remain unchanged

## Result

- host verifier now converges to an actual result in bounded time
- live verification can use host mode as evidence again instead of treating it
  as a hanging environment path
