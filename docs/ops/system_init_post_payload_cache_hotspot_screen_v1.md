# System Init Post Payload Cache Hotspot Screen v1

## Goal

Re-rank `system.init` after the scene target payload cache recovery so the next
batch follows the new dominant residual instead of continuing to optimize an
inner loop that has already been compressed.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: post payload-cache startup-profile hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: the smart_construction_core payload loop has already dropped
  materially, so the next batch must target the current top-level residual

## Live Ranking After Payload-Loop Recovery

Real `wutao/demo` login probe on the current runtime:

- `prepare_runtime_context.load_capabilities_for_user`: about `1077ms`
- `capability_load.runtime_query_registry_build`: about `1020ms`
- `capability_load.runtime_query_registry.load_capability_contributions`: about `999ms`
- `capability_load.runtime_query_registry.load_capability_contributions.native_projection`: about `717ms`
- `prepare_runtime_context.apply_extension_fact_contributions`: about `197ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension_loop_total`: about `179ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.import_and_provider`: about `175ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.loop_resolve_capability_entry_target_payload`: about `127ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.provider.payload.scene_target_payload`: about `124ms`

## Decision

The scene target payload loop is no longer the main owner of `system.init`.

The next dominant residual is now the outer capability-loading shell:

- `prepare_runtime_context.load_capabilities_for_user`
- `capability_load.runtime_query_registry_build`
- `capability_load.runtime_query_registry.load_capability_contributions`
- `capability_load.runtime_query_registry.load_capability_contributions.native_projection`

This means the next batch should move upward and re-screen the runtime query
registry build path and native projection path, rather than continuing inside
`capability_scene_targets.py`.

## Non-Targets

The next batch should not reopen:

- scene target payload cache
- provider selection cache
- provider registration cache
- content engine load cache

Those segments are no longer the dominant startup owner.
