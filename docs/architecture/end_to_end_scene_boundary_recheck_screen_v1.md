# End-to-End Scene Boundary Recheck Screen v1

## Goal

Re-evaluate the remaining frontend/backend boundary gaps after backend
action-only scene semantic supply H.

This screen decides the strongest now-supportable statement about scene-oriented
contract alignment without reopening a broad repository scan.

## Fixed Architecture Declaration

- Layer Target: Cross-layer governance screen
- Module: end-to-end scene boundary recheck
- Module Ownership: frontend/backend scene contract boundary
- Kernel or Scenario: scenario
- Reason: backend semantic supply has landed for the previously frozen
  action-only entry gap, so the boundary claim must be rechecked before any
  stronger completion statement is used

## Recheck Basis

This recheck uses only:

- `route_convergence_entry_recheck_screen_v1.md`
- `backend_action_only_scene_semantic_supply_screen_v1.md`
- `action_only_scene_semantic_supply_h_v1.md`
- latest bounded code state of:
  - `addons/smart_construction_scene/core_extension.py`
  - `addons/smart_construction_scene/services/capability_scene_targets.py`
  - `addons/smart_construction_core/services/capability_registry.py`

## Recheck Result

### 1. The previously frozen action-only scene identity gap is now materially reduced on the backend mainline

Observed updated state:

- backend navigation scene maps are no longer limited to the hand-maintained
  static lists; they now derive from scene registry `target` definitions before
  applying explicit overrides
- capability entry target supply can now derive `scene_key` from explicit
  `action_xmlid`, `menu_xmlid`, or `model + view` target hints
- released capability `entry_target` now becomes scene-first at construction
  time, not only in a later payload-resolution step

Recheck decision:

- the bounded backend gap frozen by the previous route-convergence recheck is
  no longer present in the same form
- backend scene-orchestration now owns and supplies scene identity for a wider
  set of action-only entries on the mainline

### 2. This is strong evidence of boundary alignment, but still weaker than proving every compatibility bridge is gone

Observed bounded state:

- frontend still retains compatibility route registrations and internal bridge
  mechanics by design
- this recheck did not rerun live end-to-end portal or browser smoke flows
- the proof here is bounded to contract and orchestration supply surfaces, not a
  fresh runtime inventory of every possible consumer path

Why this matters:

- backend semantic supply closure and route-shape removal are not the same
  claim
- clearing the action-only supply gap means the architecture boundary is much
  better aligned, but it does not automatically prove that every compatibility
  surface has already become removable

## Final Decision

The strongest now-supportable statement is:

> the main frontend/backend scene boundary is now aligned on the primary
> contract-consumer line, including the previously frozen action-only scene
> identity gap; however, compatibility bridges still exist as transitional
> runtime surfaces, so it is more accurate to say "main boundary aligned" than
> "all compatibility route forms fully retired".

## Frozen Next-Step Direction

If the team wants stronger proof than "main boundary aligned", the next batch
should be a bounded live/runtime verification line focused on:

1. whether remaining compatibility routes are still exercised in ordinary flows
2. whether any compatibility bridge still lacks backend scene identity support
3. whether any retained bridge can now move from compatibility to deprecation
