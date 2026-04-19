# System Init Post Provider Recovery Hotspot Screen v1

## Goal

Re-screen the live `system.init` startup profile after provider-selection
recovery so the next optimization batch does not keep targeting an already
collapsed segment.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: post provider-recovery startup-profile hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: provider selection has been reduced to negligible warm-runtime cost,
  so the next batch must follow the current live cold-path hotspot instead of
  stale timing assumptions

## Verified Input Facts

After the provider availability cache verification batch:

- cold:
  - `engine_loader_call`: about `59ms`
  - `engine.resolve_scene_provider_path`: about `30ms`
  - `engine.resolve.registry_get_provider`: about `8ms`
  - `engine.load_scene_provider_registry`: about `13ms`
- warm:
  - all four timings above collapse to `0ms`

This confirms provider-selection is no longer the dominant warm-runtime cost.

## Warm Live Ranking

A real `wutao/demo` login probe on the current live runtime shows the leading
timings are now:

- `prepare_runtime_context.load_capabilities_for_user`: about `248ms`
- `capability_load.runtime_query_registry_build`: about `243ms`
- `capability_load.runtime_query_registry.load_capability_contributions`: about `241ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.import_and_provider`: about `116ms`
- `capability_load.runtime_query_registry.load_capability_contributions.native_projection`: about `112ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.loop_resolve_capability_entry_target_payload`: about `85ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.scene_target_payload`: about `84ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.resolve_scene_map`: about `60ms`

## Fresh-Runtime Cold Ranking

After one fresh runtime restart and the first real `system.init` request:

- `prepare_runtime_context.load_capabilities_for_user`: about `376ms`
- `capability_load.runtime_query_registry_build`: about `369ms`
- `capability_load.runtime_query_registry.load_capability_contributions`: about `367ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension_loop_total`: about `219ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.import_and_provider`: about `218ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.loop_resolve_capability_entry_target_payload`: about `187ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.scene_target_payload`: about `185ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.resolve_scene_map`: about `143ms`
- `capability_load.runtime_query_registry.load_capability_contributions.native_projection`: about `134ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.scene_registry.load_scene_registry_content_entries`: about `86ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.scene_registry.content_entries.engine_loader_call`: about `63ms`

## Ownership Decision

The next meaningful residual is no longer the provider registry or provider
availability path.

The next batch should focus on the cold-path residual above it, specifically the
`smart_construction_core` capability contribution loop:

- `extension.smart_construction_core.import_and_provider`
- `provider.loop_resolve_capability_entry_target_payload`
- `provider.payload.scene_target_payload`
- `provider.payload.resolve_scene_map`

These timings still dominate the remaining cold path even after the provider
selection segment has been recovered.

## Explicit Non-Targets

The next batch should not reopen:

- provider availability caching
- provider registry module caching
- provider registration path checks
- content module caching

Those segments have already been reduced to negligible warm-runtime cost and no
longer justify the next optimization turn.
