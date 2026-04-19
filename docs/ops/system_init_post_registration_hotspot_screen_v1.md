# System Init Post Registration Hotspot Screen v1

## Goal

Reclassify the dominant live `system.init` hotspot after provider registration
has been reduced to near-zero on warm requests.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: post-registration hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: the provider registration slice has been recovered, so the next step
  must move back up to the wider scene/content pipeline

## Inherited Facts

Fresh verification now shows the provider registration slice is effectively
closed on warm runtime calls:

- `register_from_modules.path_check_hit`: `0ms`
- `register_from_modules.load_module`: `0ms`
- `register_from_modules.registrar_exec`: `0ms`

## Ownership Decision

The next batch should not revisit:

- register dedup/path key work
- registrar module caching
- provider-registry module caching
- registrar path checks

The next batch should instead reopen the wider live timing surface and assign
the new dominant hotspot at the `scene_registry.content_entries`,
`resolve_scene_map`, or adjacent higher-level runtime stages.

## Warm Live Reclassification Result

Fresh warm live `system.init` timing now shows the dominant path has moved back
up to the scene content pipeline:

- `provider.loop_resolve_capability_entry_target_payload`: about `1150ms`
- `provider.payload.scene_target_payload`: about `1149ms`
- `provider.payload.resolve_scene_map`: about `1117ms`
- `scene_registry.load_scene_registry_content_entries`: about `1055ms`
- `content_entries.engine_loader_call`: about `1043ms`
- `scene_registry.load_from_db`: about `39ms`

This means the provider registration slice is no longer the meaningful
bottleneck. The next batch should target the residual
`scene_registry.content_entries` path itself, especially the content-module
loading / entry materialization envelope rather than database loading.
