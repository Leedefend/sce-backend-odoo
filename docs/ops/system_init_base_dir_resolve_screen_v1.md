# System Init Residual base_dir.resolve() Screen v1

## Goal

Screen the remaining first `base_dir.resolve()` cost inside
`smart_scene/core/scene_provider_registry.py` after the redundant fallback
resolve was removed.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: scene provider registry residual resolve ownership screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: the previous optimization batch already removed the redundant second
  resolve call, so the next batch must decide whether the remaining first
  resolve should be reduced by caller normalization, local caching, or a path
  short-circuit

## Inherited Facts

- `_resolve_addons_root.base_dir_resolve`: about `855ms`
- `_resolve_addons_root.fallback_second_resolve`: `0ms`
- `resolve.build_scene_provider_registry`: about `1204ms`
- `resolve_scene_provider_path`: about `1206ms`

## Bounded Code-Inspection Result

The remaining hotspot sits in this narrow path:

1. `smart_construction_scene/scene_registry.py:_load_scene_registry_content_entries_with_timings()`
2. `smart_scene/core/scene_registry_engine.py:load_scene_registry_content_entries_with_timings(base_file)`
3. `smart_scene/core/scene_provider_registry.py:resolve_scene_provider_with_timings("scene.registry", base_file)`
4. `smart_scene/core/scene_provider_registry.py:_resolve_addons_root_with_timings(base_dir)`

Within that chain, the current `base_dir` is not arbitrary user input. It is
passed from module-local `Path(__file__)` style callers on the scene registry
loading path, and the helper only needs to find the enclosing `addons`
directory.

Bounded inspection also shows:

- `_resolve_addons_root(base_dir)` is only used inside
  `smart_scene/core/scene_provider_registry.py`
- the current performance chain reaches it from
  `scene_registry_engine.load_scene_registry_content_entries_with_timings(...)`
- `register_fallback_providers` and `register_from_modules` are no longer the
  bottleneck

## Ownership Decision

The remaining `base_dir.resolve()` hotspot is still a scene-orchestration
runtime concern, not a business-fact issue.

The next batch should stay narrowly inside
`smart_scene/core/scene_provider_registry.py` and evaluate one of these safe
directions:

1. normalize the caller path once and pass a pre-resolved directory/file path
2. add a tiny local cache keyed by the incoming `base_dir`
3. short-circuit the mounted-path case only when the helper can prove the path
   already sits under `addons`

## Excluded Directions

The next batch should not:

- rewrite scene registry loading semantics
- change provider registration rules
- expand into frontend or business modules
- mirror this optimization into `nav_policy_registry.py` in the same batch

## Recommended Next Step

Open one low-risk runtime screen-or-implementation batch on
`smart_scene/core/scene_provider_registry.py` to compare:

- local cache keyed by `str(base_dir)`
- caller-side normalization before `_resolve_addons_root(...)`

The first runtime change should remain additive and preserve identical
provider-path resolution semantics.

## Absolute Addons Path Optimization Result

The follow-up runtime batch implemented the narrowest safe direction from this
screen:

- if `base_dir` is already absolute and its path parts already contain
  `addons`, `_resolve_addons_root(...)` now returns that enclosing `addons`
  path without calling `Path.resolve()`
- all other cases still fall back to the previous resolve-based logic

### Updated Ownership Decision

The next live probe should verify whether the common mounted workspace path now
avoids the remaining `base_dir.resolve()` cost. If more latency remains after
that, the next candidate is no longer fallback semantics inside
`_resolve_addons_root(...)`; it is the larger provider-registry module load
path above it.
