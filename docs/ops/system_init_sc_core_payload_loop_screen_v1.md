# System Init smart_construction_core Payload Loop Screen v1

## Goal

Map the remaining `smart_construction_core` capability contribution residual to
the smallest defensible next optimization target.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: smart_construction_core capability payload loop screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: post provider-recovery evidence shows the next dominant cold-path
  residual now sits in the capability payload loop rather than in provider
  selection or content-module loading

## Live Evidence Anchor

Fresh-runtime cold ranking after provider-selection recovery:

- `extension.smart_construction_core.import_and_provider`: about `218ms`
- `provider.loop_resolve_capability_entry_target_payload`: about `187ms`
- `provider.payload.scene_target_payload`: about `185ms`
- `provider.payload.resolve_scene_map`: about `143ms`
- `provider.payload.scene_registry.load_scene_registry_content_entries`: about `86ms`
- `provider.payload.scene_registry.content_entries.engine_loader_call`: about `63ms`

These values show the residual is concentrated inside the capability payload
loop, with the provider-selection segment already reduced to low double-digit
or zero cost.

## Code Mapping

### 1. Outer extension shell

`addons/smart_core/app_config_engine/capability/core/contribution_loader.py`

- `load_capability_contributions_with_timings(...)`
- `extension.{module}.import_and_provider`

This outer timing wraps extension import plus provider execution.

### 2. smart_construction_core provider loop

`addons/smart_construction_core/services/capability_registry.py`

- `list_capabilities_for_user_with_timings(...)`
- `loop_resolve_capability_entry_target_payload`

Inside the capability definition loop, each visible capability calls
`resolve_capability_entry_target_payload_with_timings(...)` and accumulates its
cost into `loop_resolve_capability_entry_target_payload`.

### 3. Scene payload resolver

`addons/smart_construction_scene/services/capability_scene_targets.py`

- `resolve_capability_entry_target_payload_with_timings(...)`
- `resolve_scene_map`
- `scene_target_payload`

When a capability has `scene_key`, this function calls
`scene_registry.load_scene_configs_with_timings(env)`, rebuilds a `scene_map`
dictionary, then resolves route/action/menu payload.

## Decision

The most likely next optimization target is not the outer `import_and_provider`
shell itself. The outer shell is largely explained by repeated inner payload
resolution.

The tight next target is:

- `resolve_capability_entry_target_payload_with_timings(...)`

More specifically, the repeated per-capability call to:

- `scene_registry.load_scene_configs_with_timings(env)`
- rebuild of `scene_map = {... for scene in scenes ...}`

inside that resolver appears to be the current dominant cold-path residual.

## Non-Targets

The next batch should not reopen:

- provider availability checks
- provider registry loading
- provider registration path checks
- content engine module caching

Those segments are no longer the main cold-path driver.

## Recommended Next Batch

Open one bounded runtime optimization batch on:

- `addons/smart_construction_scene/services/capability_scene_targets.py`

with the explicit goal of avoiding repeated scene-config loading / scene-map
rebuild work across visible capability definitions during one `system.init`
request, without changing capability semantics or frontend contracts.
