# Backend Scene Record Entry Contract Implement v1

## Goal

Materialize one additive `record_entry` envelope under backend scene-oriented
`entry_target` so concrete record identity can travel through scene contracts
without becoming a parallel public authority family.

## Scope

- `addons/smart_core/core/system_init_payload_builder.py`
- `addons/smart_core/governance/scene_normalizer.py`
- `addons/smart_core/identity/identity_resolver.py`
- focused backend tests only

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer
- Module: generic scene-carried record entry contract
- Module Ownership: `smart_core`
- Kernel or Scenario: kernel
- Reason: add the missing consumption-ready record-entry envelope while keeping
  `scene_key` as the only public authority field

## Implementation Rule

- `entry_target.type` remains `scene`
- `entry_target.scene_key` remains the public authority field
- `entry_target.record_entry` is additive context only
- `record_entry` may be emitted only when backend already knows concrete record
  identity

## Implemented Changes

- `system_init_payload_builder` now emits `entry_target.record_entry` when scene
  authority already carries both `model` and `record_id`
- `scene_normalizer` now materializes the same `record_entry` envelope for scene
  target output after xmlid resolution, keeping `scene_key` as the only public
  authority and preserving legacy refs under `compatibility_refs`
- `identity_resolver.infer_default_route_from_nav` now forwards
  `meta.model/meta.record_id/meta.action_id` into the additive `entry_target`
  payload when navigation metadata already knows a concrete record
- focused tests now assert the new `record_entry` envelope on startup, scene
  normalization, and inferred default-route output
