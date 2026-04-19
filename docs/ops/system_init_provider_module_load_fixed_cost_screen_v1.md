# System Init Provider Module Load Fixed Cost Screen v1

## Goal

Narrow the remaining ~380ms fixed cost inside
`scene_provider_registry._register_from_modules(...)` after both cache
recoveries above it have landed.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider module-load residual fixed cost screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: warm verification proves the higher-level module caches are working,
  so the remaining cost now sits inside the residual register_from_modules
  shell

## Inherited Facts

After the latest engine-level cache and path-derivation recovery:

- cold:
  - `engine.load_scene_provider_registry`: about `17ms`
  - `register_from_modules.load_module`: about `383ms`
- warm:
  - `engine.load_scene_provider_registry`: `0ms`
  - `register_from_modules.load_module`: about `379ms`

## Classification

The higher-level provider-registry cache is now effective. The remaining
~380ms does not come from rebuilding `scene_provider_registry.py` itself.

So the next likely candidates are now inside `_register_from_modules(...)`:

1. repeated `path.exists()` / `path.is_file()` on mounted addon paths
2. residual `_load_module(...)` shell even when its internal module cache hits
3. candidate/path derivation work before `_load_module(...)` is called

## Ownership Decision

The next batch should stay narrowly inside
`smart_scene/core/scene_provider_registry.py:_register_from_modules(...)` and
split the remaining load-module envelope before another optimization.

## Residual Module-Load Timing Split Result

The follow-up runtime batch now exposes residual module-load sub-stages for:

- `register_from_modules.candidate_derivation`
- `register_from_modules.path_check_hit`
- `register_from_modules.path_check_missing`
- `register_from_modules.load_module.cache_lookup`
- `register_from_modules.load_module.cache_hit`
- `register_from_modules.load_module.cache_miss_spec`
- `register_from_modules.load_module.cache_miss_module_from_spec`
- `register_from_modules.load_module.cache_miss_exec_module`

This means the next live probe can assign the remaining ~380ms shell cost to
path checks, candidate setup, or the residual cache-hit path itself.

## Module Path Check Optimization Result

The follow-up runtime batch now caches absolute registrar module file-check
results by `str(path)` inside `scene_provider_registry.py`.

This keeps registrar semantics unchanged while removing repeated
`path.exists()/is_file()` cost for static absolute module paths on warm
requests.
