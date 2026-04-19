# System Init Live Codepath Screen v1

## Goal

Inspect the live dev container codepath that reaches
`_resolve_addons_root_with_timings(...)` and explain why the absolute-path fast
path did not reduce live `base_dir.resolve()` timings.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: live container provider-registry codepath screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: refreshed live timing still showed `base_dir.resolve()` cost, so the
  next step had to inspect the live container codepath rather than keep editing
  `_resolve_addons_root(...)` blindly

## Inherited Facts

- Refreshed live probe still reported:
  - `resolve.build_scene_provider_registry`: about `1138ms`
  - `resolve.registry.resolve_addons_root.fast_absolute_addons_lookup`: `0ms`
  - `resolve.registry.resolve_addons_root.base_dir_resolve`: about `798ms`
  - `resolve.registry.resolve_addons_root.fallback_second_resolve`: `0ms`

## Live Container Inspection Result

The running container exposes addon code under:

- `/mnt/extra-addons/...`

Read-only inspection of the live file confirmed:

- `/mnt/extra-addons/smart_scene/core/scene_provider_registry.py`
  contains `_resolve_addons_root_from_absolute_parts(...)`
- that helper only matches path parts equal to `addons`

Read-only runtime probe inside the same container confirmed:

- sample path:
  `/mnt/extra-addons/smart_construction_scene/scene_registry.py`
- `sample.is_absolute() = True`
- `_resolve_addons_root_from_absolute_parts(sample) -> None`
- `_resolve_addons_root(sample) -> /`

## Classification

The fast path is active in the live container, but it does not match the live
mount layout because the container uses `extra-addons`, not `addons`.

So the remaining live `base_dir.resolve()` cost is not caused by:

- stale runtime state
- relative `base_file`
- missing code deployment

It is caused by an incomplete path-shape assumption inside the fast path.

## Ownership Decision

The next low-risk runtime batch should stay narrowly inside
`smart_scene/core/scene_provider_registry.py` and extend the absolute-path fast
path to recognize the live addon mount names used by the running container,
starting with `extra-addons`.

## Live Addon-Root Optimization Result

The follow-up runtime batch extended the absolute-path fast helper from one
name to the live mount-name set:

- `addons`
- `extra-addons`
- `addons_external`

This keeps the optimization local to the helper while covering the live
container layout that the running dev runtime actually uses.
