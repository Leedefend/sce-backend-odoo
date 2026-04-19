# System Init Provider Module Load Screen v1

## Goal

Narrow the remaining provider registration hotspot inside
`smart_scene/core/scene_provider_registry.py:_register_from_modules(...)`.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: provider registrar module-load hotspot screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: fresh live verification shows registration internals have been
  recovered except for module loading in `_register_from_modules(...)`

## Inherited Facts

Fresh live `system.init` timings now show:

- `register.provider_path_resolve`: about `2ms`
- `register.total`: about `2ms`
- `register.duplicate_scan`: `0ms`
- `register_fallback_providers`: about `2ms`
- `register_from_modules`: about `2215ms`
- `register_from_modules.load_module`: about `2190ms`
- `register_from_modules.registrar_exec`: about `3ms`

## Bounded Code-Inspection Result

Inside `smart_scene/core/scene_provider_registry.py`:

1. `_registration_module_candidates(...)` currently returns one registrar module
2. `_register_from_modules(...)` checks `path.exists()` / `path.is_file()`
3. `_load_module(path, module_name)` does:
   - `spec_from_file_location(...)`
   - `module_from_spec(...)`
   - `spec.loader.exec_module(module)`
4. the loaded registrar then executes quickly relative to module load itself

This means the current hotspot is not registrar business logic. It is the
dynamic Python module load path itself.

## Ownership Decision

The next batch should stay inside `scene_provider_registry.py` and target only
the module-load path, for example by reusing loaded registrar modules inside the
process instead of rebuilding them on each request.

## Provider Module Cache Result

The follow-up runtime batch now caches loaded registrar modules by
`(module_name, str(path))` inside `scene_provider_registry.py`.

This keeps registrar semantics unchanged while allowing warm runtime calls to
reuse the already-loaded module instead of paying repeated
`spec_from_file_location(...) -> exec_module(...)` cost.
