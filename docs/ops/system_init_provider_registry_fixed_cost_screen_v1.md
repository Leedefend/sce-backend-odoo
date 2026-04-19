# System Init Provider Registry Fixed Cost Screen v1

## Goal

Narrow the remaining 300-400ms provider-registry/module-load envelope after the
cross-request cache boundary recovery.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider-registry fixed envelope cost screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: the previous cache recoveries removed the seconds-level hotspot, so
  the next batch must target only the smaller residual shell cost

## Inherited Facts

Cold live probe after the latest engine-level cache recovery:

- `engine.load_scene_provider_registry`: about `389ms`
- `engine.resolve.build_scene_provider_registry`: about `424ms`
- `register_from_modules.load_module`: about `412ms`

Warm live probe on the same runtime:

- `engine.load_scene_provider_registry`: about `369ms`
- `engine.resolve.build_scene_provider_registry`: about `394ms`
- `register_from_modules.load_module`: about `378ms`

## Classification

The cache boundary recovery clearly worked because the previous seconds-level
hotspot collapsed into a few hundred milliseconds. The remaining fixed cost now
appears to be one of:

1. repeated `base_file.resolve()` and registry-path derivation in
   `scene_registry_engine._load_scene_provider_registry(...)`
2. the residual provider-registry rebuild shell that still runs even when the
   module object is cached
3. a smaller remaining module-cache lookup/importlib envelope

## Ownership Decision

The next batch should stay narrowly inside the provider-registry envelope and
split or optimize the remaining fixed shell cost without revisiting:

- addon-root detection
- register dedup/path key work
- registrar business logic

## Fixed Shell Optimization Result

The follow-up runtime batch now removes the common absolute-path filesystem
resolution from `scene_registry_engine._load_scene_provider_registry(...)`:

- derived `scene_provider_registry.py` paths are cached by `str(base_file)`
- absolute `base_file` values use `parents[1]` directly instead of
  `base_file.resolve()`

This keeps the higher-level module cache behavior unchanged while shrinking the
remaining fixed shell work around provider-registry lookup.
