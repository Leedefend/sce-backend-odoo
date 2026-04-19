# System Init Provider Registry Module Cache Screen v1

## Goal

Classify why registrar module caching inside
`smart_scene/core/scene_provider_registry.py` does not reduce warm-request
`load_module` timings.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider registry module cache boundary screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: warm verification shows the lower-level registrar cache is not the
  real cross-request cache boundary

## Inherited Facts

- First fresh live probe after restart showed:
  - `register_from_modules.load_module`: about `2035ms`
- Second warm live probe on the same runtime still showed:
  - `register_from_modules.load_module`: about `2084ms`

## Bounded Code-Inspection Result

Inside `smart_scene/core/scene_registry_engine.py`:

1. `_load_scene_provider_registry(base_file)` still performs
   `spec_from_file_location(...) -> module_from_spec(...) -> exec_module(...)`
   on every call
2. that means `scene_provider_registry.py` is rebuilt as a fresh module object
   per request
3. module globals inside `scene_provider_registry.py`, including the new
   `_LOADED_PROVIDER_MODULES` cache, do not survive across requests if the
   parent module itself is recreated each time

## Ownership Decision

The next batch should not refine `_load_module(...)` again.

The next low-risk optimization should move the cache boundary upward into
`scene_registry_engine._load_scene_provider_registry(...)`, so the
provider-registry module object itself can be reused across warm requests.

## Provider Registry Module Cache Result

The follow-up runtime batch now caches the loaded
`scene_provider_registry.py` module by resolved file path inside
`scene_registry_engine.py`.

This moves the cache boundary to the first dynamic-load hop, so warm requests
can reuse the same provider-registry module object and preserve lower-level
registrar module caches across requests.
