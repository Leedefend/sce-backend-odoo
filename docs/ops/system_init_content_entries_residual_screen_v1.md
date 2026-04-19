# System Init Content Entries Residual Screen v1

## Goal

Narrow the remaining ~1.0-1.1s hotspot inside the
`scene_registry.load_scene_registry_content_entries(...)` /
`content_entries.engine_loader_call` path after provider registration recovery.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: content_entries residual hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: fresh warm live timings prove the dominant hotspot has moved back up
  to the scene content pipeline

## Inherited Facts

Fresh warm live timing now shows:

- `provider.payload.resolve_scene_map`: about `1117ms`
- `scene_registry.load_scene_registry_content_entries`: about `1055ms`
- `content_entries.engine_loader_call`: about `1043ms`
- `scene_registry.load_from_db`: about `39ms`

## Ownership Decision

The next batch should not revisit provider registration.

The next batch should stay inside the content entry loading path and split the
remaining envelope between:

1. content module load
2. `list_scene_entries()` execution
3. row filtering/validation

## Warm Live Reclassification Result

Fresh warm live timing confirms the residual hotspot is still concentrated in
the engine-side content entry load envelope:

- `content_entries.engine_loader_call`: about `1073ms`
- `provider.payload.resolve_scene_map`: about `1117ms`
- `scene_registry.load_scene_registry_content_entries`: about `1055ms`

Code inspection also confirms the detailed stage names already exist on the
engine side under the `engine.` prefix:

- `engine.load_scene_registry_content_module`
- `engine.list_scene_entries`
- `engine.filter_valid_rows`

So the next batch should use those existing engine-prefixed stages as the
boundary and target the content-module loading / entry materialization shell in
`smart_scene/core/scene_registry_engine.py`.

## Content Module Cache Result

The follow-up runtime batch now caches the loaded scene registry content module
by resolved provider path inside `scene_registry_engine.py`.

This keeps scene entry semantics unchanged while allowing warm requests to
reuse the same content module object instead of paying repeated
`spec_from_file_location(...) -> exec_module(...)` cost.

## Residual Content Entries Timing Split Result

The follow-up runtime batch keeps the same boundary and sharpens the remaining
content entry envelope into:

- `load_scene_registry_content_module`
- `list_scene_entries`
- `filter_valid_rows`

This means the next live probe can assign the residual ~1.0s hotspot to one of
those concrete sub-stages instead of the whole content_entries shell.
