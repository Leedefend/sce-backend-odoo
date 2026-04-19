# System Init Scene Registry Base File Screen v1

## Goal

Screen why the live `system.init` probe still reports
`_resolve_addons_root.base_dir_resolve` after the absolute-addons fast path was
implemented.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: scene registry engine live base_file mismatch screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: local inspection proves the scene registry caller passes an absolute
  `Path(__file__)`, so the live mismatch must be classified before any more
  runtime code changes

## Inherited Facts

- Local probe importing `addons/smart_construction_scene/scene_registry.py`
  reports:
  - `__file__ = /mnt/e/sc-backend-odoo/addons/smart_construction_scene/scene_registry.py`
  - `Path(__file__).is_absolute() = True`
- Live `system.init` probe still reports:
  - `resolve.registry.resolve_addons_root.fast_absolute_addons_lookup = 0`
  - `resolve.registry.resolve_addons_root.base_dir_resolve = 713`

## Bounded Inspection Result

The scene registry loading path still calls:

1. `smart_construction_scene/scene_registry.py`
   `_load_scene_registry_content_entries_with_timings()`
2. `smart_scene/core/scene_registry_engine.py`
   `load_scene_registry_content_entries_with_timings(base_file)`
3. `smart_scene/core/scene_provider_registry.py`
   `_resolve_addons_root_with_timings(base_dir)`

Local import inspection proves the direct caller path is already absolute, so
the fast path should be eligible in a fresh runtime.

## Classification

At this point there are only two credible explanations:

1. the live runtime on `localhost:8069` is still running pre-optimization code
2. the live request is hitting a different process/runtime copy than the local
   workspace file that was edited

The earlier hypothesis that `base_file` itself is non-absolute is no longer
supported by local evidence.

## Ownership Decision

The next batch should not re-edit `_resolve_addons_root(...)`.

The next low-risk step is a live verification batch that refreshes the running
backend process and then reruns the same `system.init` timing probe. Only after
that refresh should the team decide whether more provider-registry changes are
needed.
