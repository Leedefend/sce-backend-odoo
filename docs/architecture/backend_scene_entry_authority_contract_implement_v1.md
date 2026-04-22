# Backend Scene Entry Authority Contract Implement V1

## Goal

Materialize one additive public `entry_target` surface so backend startup,
navigation, and scene target outputs all expose the same scene-oriented entry
authority.

## Scope

- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/identity/identity_resolver.py`
- `addons/smart_core/governance/scene_normalizer.py`
- focused backend tests only

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer
- Module: public scene entry target surface
- Module Ownership: `smart_core`
- Kernel or Scenario: kernel
- Reason: freeze `scene_key` as the public authority while preserving existing
  native anchors as compatibility references

## Implementation Rule

- `entry_target.type` is `scene`
- `entry_target.scene_key` is the authority field
- `menu_id/action_id/model/record_id/route` may appear only as compatibility
  refs or routing hints, not as parallel public target families

## Implemented Changes

- `system_init_payload_builder` now adds additive `entry_target` payloads to
  `default_route`, `role_surface`, and navigation node metadata when scene
  identity is available
- `identity_resolver` now emits `landing_entry_target` on `role_surface` and
  `entry_target` on inferred default-route payloads
- `scene_normalizer` now materializes `target.entry_target` for scene targets
  after xmlid resolution and semantic fallback handling
