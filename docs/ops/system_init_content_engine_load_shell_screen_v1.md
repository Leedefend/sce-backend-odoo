# System Init Content Engine Load Shell Screen v1

## Goal

Narrow the remaining ~400ms `engine_loader_call` shell after content module
load, `list_scene_entries()`, and row filtering have all been reduced to
negligible levels.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: content engine_loader_call residual shell screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: cold/warm verification proves the remaining content_entries cost is no
  longer dominated by content module execution itself

## Inherited Facts

After content module caching:

- cold:
  - `engine_loader_call`: about `440ms`
  - `engine.load_scene_registry_content_module`: about `14ms`
  - `engine.list_scene_entries`: `0ms`
  - `engine.filter_valid_rows`: `0ms`
- warm:
  - `engine_loader_call`: about `402ms`
  - `engine.load_scene_registry_content_module`: `0ms`
  - `engine.list_scene_entries`: `0ms`
  - `engine.filter_valid_rows`: `0ms`

## Ownership Decision

The next batch should not revisit:

- content module caching
- provider registration
- scene entry row filtering

The next batch should instead isolate the remaining fixed shell around
`engine_loader_call`, which now appears to live in wrapper orchestration rather
than in the direct content-module/list/filter stages.

## Provider Availability Optimization Result

The follow-up runtime batch now caches absolute provider-path availability
checks inside `scene_provider_registry.py`.

This keeps provider choice semantics unchanged while avoiding repeated
`exists()/is_file()` checks for stable absolute provider paths during
`registry_get_provider` on warm requests.

## Cold/Warm Live Verification Result

After one fresh runtime restart and real `wutao/demo` login through
`/api/v1/intent`:

- cold:
  - `engine_loader_call`: about `59ms`
  - `engine.resolve_scene_provider_path`: about `30ms`
  - `engine.resolve.registry_get_provider`: about `8ms`
  - `engine.load_scene_provider_registry`: about `13ms`
- warm:
  - `engine_loader_call`: `0ms`
  - `engine.resolve_scene_provider_path`: `0ms`
  - `engine.resolve.registry_get_provider`: `0ms`
  - `engine.load_scene_provider_registry`: `0ms`

This verifies that the residual warm shell previously observed around
`registry_get_provider` / `resolve_scene_provider_path` has been eliminated by
the provider availability cache plus the earlier registry/module cache
recoveries.

## Next Ownership Decision

Provider selection is no longer the dominant warm-runtime hotspot.

The next batch should re-screen the wider `system.init` startup profile above
the recovered provider-selection segment and identify the next meaningful
residual fixed cost in the live cold path.
