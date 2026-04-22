# Action-Only Scene Semantic Supply H v1

## Goal

Supply backend scene identity for action-only entries from the scene
orchestration layer, so frontend no longer depends on incomplete manual native
action/menu scene maps to converge those entries.

## Scope

- `addons/smart_construction_scene/core_extension.py`
- `addons/smart_construction_scene/services/capability_scene_targets.py`
- `addons/smart_construction_core/services/capability_registry.py`
- `addons/smart_construction_scene/tests/test_action_only_scene_semantic_supply.py`

## Fixed Architecture Declaration

- Layer Target: Backend scene-orchestration runtime
- Module: action-only scene identity supply
- Module Ownership: smart_construction_scene orchestration mappings
- Kernel or Scenario: scenario
- Reason: route-convergence recheck has frozen the remaining gap as action-only
  entries without enough emitted scene identity

## Implemented Changes

- `smart_core_nav_scene_maps()` now derives `menu_scene_map`,
  `action_xmlid_scene_map`, and `model_view_scene_map` from scene registry
  `target` definitions before applying the existing explicit overrides
- `capability_scene_targets` now derives `scene_key` from explicit
  `action_xmlid`, `menu_xmlid`, or `model+view_type/view_mode` when the
  capability does not already carry an explicit or hardcoded scene mapping
- `capability_registry` now passes `env` into `build_capability_entry_target()`
  so the released `entry_target` surface itself becomes scene-first, not just
  the resolved payload

## Result

- action-only entries backed by scene registry targets can now emit scene
  identity through backend orchestration without adding new business facts
- static hand-maintained nav scene maps remain valid as explicit overrides, but
  no longer act as the only source of truth
- the backend has moved one step closer to a full scene-oriented public entry
  surface
