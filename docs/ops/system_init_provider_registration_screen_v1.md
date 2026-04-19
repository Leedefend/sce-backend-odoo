# System Init Provider Registration Screen v1

## Goal

Narrow the new live hotspot inside
`smart_scene/core/scene_provider_registry.py:build_scene_provider_registry(...)`
after addon-root recovery and scene-engine dedup.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider registry registration hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: fresh live timings show the remaining hotspot now sits in provider
  registration stages rather than addon-root detection or duplicate engine load

## Inherited Facts

Fresh live `system.init` timings now show:

- `engine.resolve.build_scene_provider_registry`: about `22392ms`
- `engine.resolve.registry.register_fallback_providers`: about `7799ms`
- `engine.resolve.registry.register_from_modules`: about `14561ms`
- `engine.load_scene_provider_registry`: about `2273ms`

## Bounded Code-Inspection Result

Inside `smart_scene/core/scene_provider_registry.py`:

1. `_register_fallback_providers(...)` registers four candidate providers
2. each registration calls `SceneProviderRegistry.register(...)`
3. `register(...)` computes:
   - `provider.normalized_scene_key()`
   - `provider.provider_path.resolve()` for the dedup key
   - another `item.provider_path.resolve()` for every existing row in that
     scene bucket during duplicate checks
   - a sort on each append
4. `_register_from_modules(...)` dynamically loads each registrar module via
   `_load_module(...)`, then runs `register_scene_content_providers(...)`, which
   may in turn call `registry.register(...)` repeatedly

So the likely next hotspot candidates are:

1. repeated `Path.resolve()` inside `SceneProviderRegistry.register(...)`
2. repeated list dedup scans and resorting during registration
3. registrar module execution inside `_register_from_modules(...)`

## Ownership Decision

The next batch should stay inside
`smart_scene/core/scene_provider_registry.py` and split these registration
stages before choosing an optimization:

- fallback registration shell vs `registry.register(...)`
- module import vs registrar execution
- register dedup key resolution vs duplicate scan vs sort

## Registration Timing Split Result

The follow-up runtime batch now exposes timing hooks for:

- `register_fallback_providers.project_dashboard`
- `register_fallback_providers.scene_registry`
- `register_from_modules.load_module`
- `register_from_modules.registrar_exec`
- `register.normalized_scene_key`
- `register.provider_path_resolve`
- `register.duplicate_scan`
- `register.sort_rows`
- `register.total`

This means the next live probe can assign the remaining registration hotspot to
module loading, registrar execution, or per-registration dedup/sort work rather
than the whole registration envelope.

## Register Dedup Optimization Result

The follow-up runtime batch now removes the two hottest registration internals:

- resolved provider paths are cached by raw `str(provider.provider_path)`
- duplicate checks use a per-scene `set[(provider_key, resolved_path)]` instead
  of rescanning existing rows and re-resolving their paths

Priority ordering and final row sort semantics remain unchanged.

## Provider Path Key Optimization Result

The follow-up runtime batch now treats already-absolute provider paths as
identity keys directly and preserves the old `resolve()` behavior only for
non-absolute paths.

That keeps registration semantics stable for the current live addon-root layout
while removing filesystem resolve cost from the common absolute-path case.
