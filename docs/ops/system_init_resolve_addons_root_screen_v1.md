# System Init Resolve Addons Root Screen v1

## Goal

Screen the real ownership inside `_resolve_addons_root(base_dir)` before opening
an optimization batch.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: scene provider registry addons-root ownership screen
- Module Ownership: existing backend code inspection + docs
- Kernel or Scenario: scenario
- Reason: the previous provider-registry timing batch proved
  `_resolve_addons_root(base_dir)` dominates that path, so the next batch must
  target the real path-resolution sub-step

## Inherited Facts

- `resolve.build_scene_provider_registry`: about `1996ms`
- `resolve.registry.resolve_addons_root`: about `1949ms`
- `register_fallback_providers`: about `16ms`
- `register_from_modules`: `0ms`

## Code-Inspection Result

`_resolve_addons_root(base_dir)` currently does:

1. `current = base_dir.resolve()`
2. if `current.is_file()`, switch to `current.parent`
3. iterate `[current] + list(current.parents)`
4. return the first parent whose name is `"addons"`
5. otherwise fallback to `base_dir.resolve().parents[2]`

The high-probability cost centers are:

1. repeated `Path.resolve()` on `/mnt/e/...` paths
2. materializing `list(current.parents)` on every call
3. a second `base_dir.resolve()` on the fallback branch

The structurally cheap parts are:

- checking `parent.name == "addons"`
- branching on `current.is_file()` once `current` is already resolved

## Ownership Decision

The next runtime batch should instrument `_resolve_addons_root(base_dir)` into:

1. first `base_dir.resolve()`
2. optional `current.is_file()` / parent adjustment
3. parent iteration / search for `"addons"`
4. fallback second `base_dir.resolve().parents[2]`

The highest-probability hotspot is the first `Path.resolve()` on the mounted
workspace path.

## Follow-up Timing Result

The follow-up instrumentation batch has now split `_resolve_addons_root`:

- `base_dir_resolve`: about `860ms`
- `fallback_second_resolve`: about `864ms`
- `adjust_file_parent`: `0ms`
- `materialize_parent_chain`: `0ms`
- `scan_parent_chain`: `0ms`

## Updated Ownership Decision

The hotspot is now assigned precisely:

1. first `Path.resolve()`
2. fallback second `Path.resolve()`

The next optimization batch should target eliminating the second resolve or
otherwise reducing repeated resolve calls on the mounted workspace path.
