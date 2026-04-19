# System Init Provider Registry Next Screen v1

## Goal

Classify the next live hotspot above `_resolve_addons_root(...)` now that fresh
live verification no longer shows `base_dir.resolve()` timing output.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider registry next hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: the addon-root helper has been recovered in live runtime, so the next
  batch must move upward to the larger provider-registry/module-load path

## Inherited Facts

- Fresh live probe after the `extra-addons` fast-path update shows:
  - `resolve.build_scene_provider_registry`: about `22307ms`
  - `resolve_scene_provider_path`: about `23195ms`
  - `resolve.registry.resolve_addons_root.fast_absolute_addons_lookup`: `0ms`
  - `resolve.registry.resolve_addons_root.base_dir_resolve`: absent from output
- This means `_resolve_addons_root(...)` is no longer the measurable live
  hotspot on the fresh runtime path.

## Classification

The next hotspot now sits above the addon-root helper, most likely in one of
these stages:

1. provider-registry rebuild around `_register_fallback_providers(...)` and
   `_register_from_modules(...)`
2. repeated dynamic module loading in
   `scene_registry_engine._load_scene_provider_registry(...)`
3. another cold-start effect in the larger scene registry engine path

## Bounded Code-Inspection Result

Inspection of `smart_scene/core/scene_registry_engine.py` narrows the next
candidate further.

Inside `load_scene_registry_content_entries_with_timings(base_file)`:

1. `_load_scene_provider_registry(base_file)` is called once up front and
   dynamically loads `scene_provider_registry.py` via
   `spec_from_file_location(...) -> module_from_spec(...) -> exec_module(...)`
2. after provider-path resolution succeeds, the function calls
   `load_scene_registry_content_module(base_file)`
3. `load_scene_registry_content_module(base_file)` calls
   `_load_scene_provider_registry(base_file)` again before resolving the same
   provider path

So the current cold path pays for repeated dynamic provider-registry module
loading and repeated provider-path resolution inside one higher-level scene
registry content load.

That means the most likely next hotspot is no longer addons-root detection
itself, but repeated dynamic module/bootstrap work in:

- `scene_registry_engine._load_scene_provider_registry(base_file)`
- `scene_registry_engine.load_scene_registry_content_module(base_file)`

The provider-registry rebuild path remains part of the cost surface, but the
next narrow timing batch should split engine-level repeated module loading
before changing registry registration logic again.

## Ownership Decision

The next low-risk batch should not touch `_resolve_addons_root(...)` again.

The next screen or timing batch should focus on the provider-registry rebuild
and module-load path above it, using the existing
`smart_scene/core/scene_provider_registry.py` and
`smart_scene/core/scene_registry_engine.py` timing hooks as the boundary.

More narrowly, the next runtime batch should instrument or optimize repeated
engine-level dynamic loads of `scene_provider_registry.py` and the second
provider-path resolution inside `load_scene_registry_content_module(...)`.

## Scene Engine Dedup Result

The follow-up runtime batch stayed within
`smart_scene/core/scene_registry_engine.py` and removed the repeated work
inside one content-load call:

- `load_scene_registry_content_entries_with_timings(...)` now passes the first
  loaded `registry_module` into `load_scene_registry_content_module(...)`
- the already-resolved `provider_path` is also reused instead of being
  recomputed

This keeps lookup semantics unchanged while removing the second dynamic
provider-registry load and the duplicate provider-path resolution on the same
engine path.
