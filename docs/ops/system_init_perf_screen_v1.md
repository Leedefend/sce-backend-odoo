# System Init Performance Screen v1

## Goal

Screen the ownership of the current `system.init` latency before opening a
backend implementation batch.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: `system.init` latency ownership screen
- Module Ownership: existing backend/runtime diagnostics + docs
- Kernel or Scenario: scenario
- Reason: frontend startup recovery is complete enough to show the remaining
  delay lives inside `system.init` itself

## Known Entry Facts

- direct route blank shell has been recovered into a visible startup overlay
- authenticated direct route eventually reaches `project.task` detail
- shell-side timing:
  - `5174 /api/v1/intent system.init`: about `18.1s`
  - `8069 /api/v1/intent system.init`: about `20.2s`
- payload size is about `587 KB`

## Screening Questions

1. Which internal slice dominates the current `system.init` cost:
   - nav dispatch
   - workspace home / workbench payload
   - role/capability surface assembly
   - extension provider chaining
   - preload hooks
2. Does existing `system.init.inspect` or current logging already expose enough
   timing detail to assign ownership?
3. Is the next batch a pure runtime/performance batch, or does it first need a
   deeper inspect enhancement batch?

## Screening Result

Existing diagnostics are already sufficient; no extra inspect enhancement batch
is needed before implementation.

### Real Timings

Measured against `wutao / sc_demo` with `with_preload=false` and
`root_xmlid=smart_construction_core.menu_sc_root`:

- `system.init`
  - total: `17577ms`
  - `build_nav`: `5441ms`
  - `prepare_runtime_context`: `6824ms`
  - `build_scene_runtime_surface`: `4459ms`
  - `collect_intents`: `393ms`
  - `execute_scene_runtime`: `242ms`
  - `apply_surface`: `88ms`
  - `finalize_startup_surface`: `126ms`
- `system.init.inspect`
  - total: `16658ms`
  - `build_nav`: `4699ms`
  - `prepare_runtime_context`: `6853ms`
  - `build_scene_runtime_surface`: `4323ms`
  - `collect_intents`: `348ms`
  - `execute_scene_runtime`: `229ms`
  - `apply_surface`: `76ms`
  - `finalize_startup_surface`: `125ms`

### Ownership Conclusion

The dominant latency is concentrated in three backend/runtime slices:

1. `prepare_runtime_context`
   - current top stage at about `6.8s`
   - this stage currently includes extension fact contribution merge and runtime
     context preparation inside `addons/smart_core/handlers/system_init.py`
2. `build_nav`
   - about `4.7s ~ 5.4s`
   - ownership is `NavDispatcher.build_nav()` under
     `addons/smart_core/app_config_engine/services/dispatchers/nav_dispatcher.py`
3. `build_scene_runtime_surface`
   - about `4.3s ~ 4.5s`
   - ownership is the scene/runtime surface assembly path after
     `SystemInitSceneRuntimeSurfaceBuilder.apply(...)`

What is not the dominant bottleneck:

- `execute_scene_runtime` itself is only about `0.23s`
- `apply_surface` is under `0.1s`
- `workspace_home` is effectively `0ms` with current request params
- frontend proxy overhead is not the main cause
  - `5174 proxy`: about `18.1s`
  - `8069 backend`: about `20.2s`

## Prepare Runtime Context Split Result

An instrumentation batch has now split the coarse
`prepare_runtime_context` stage into additive sub-timings under:

- `meta.startup_profile.subtimings_ms.prepare_runtime_context`

Measured again against `wutao / sc_demo` after reloading the active Odoo
container:

- total request: `21814ms`
- `prepare_runtime_context`: `7659ms`
- `prepare_runtime_context` subtimings:
  - `build_base_payload`: `7509ms`
  - `apply_extension_fact_contributions`: `147ms`
  - `initialize_scene_diagnostics`: `0ms`
  - `create_components`: `0ms`
  - `append_act_url_deprecations`: `0ms`
  - `attach_preload_when_enabled`: `0ms`
  - `merge_extension_facts`: `0ms`
  - `load_scene_validation_recovery_strategy`: `1ms`
  - `load_scene_action_surface_strategy`: `1ms`
  - `normalize_scene_action_surface_strategy`: `0ms`

### Updated Ownership Decision

The dominant cost inside `prepare_runtime_context` is no longer ambiguous:

1. `build_base_payload` wrapper around startup payload assembly
   - about `7.5s` out of `7.7s`
   - code inspection shows `SystemInitPayloadBuilder.build_base(...)` itself is a
     trivial dict return
   - the dominant cost is therefore expected to live in argument evaluation
     before the call, especially capability loading / normalization
2. extension fact contribution and strategy loading are not the main blocker
   - combined cost is about `149ms`
3. component factory and diagnostics setup are negligible in the current probe
   - each measured as `0ms` at this granularity

## Next Implementation Target

The next batch should remain a backend/runtime performance batch, not another
frontend batch.

Recommended target order:

1. open a narrow runtime optimization batch on
   `_load_capabilities_for_user(...)` / the capability-provider path because a
   second timing split shows:
   - `load_capabilities_for_user`: about `7821ms`
   - `normalize_capabilities`: about `25ms`
   - `build_base_call`: `0ms`
   - capability-load screen further narrows the next instrumentation target to:
     - native capability row projection
     - native schema normalize/validate
     - extension module enumeration/import/provider loop
     - contribution merge
     - registry snapshot build
   - capability-load timing then proves the active runtime branch is
     `runtime_query_service` at about `7285ms`, so the next concrete target is
     inside `CapabilityQueryService -> CapabilityRegistry -> load_capability_contributions(...)`
   - runtime-query timing then proves the active registry hotspot is
     `load_capability_contributions(...)` at about `8411ms`; merge, ownership,
     snapshot, and list projection are negligible
   - contribution-load timing then proves the dominant sub-step is
     `extension.smart_construction_core.import_and_provider` at about `8043ms`,
     while native projection is only about `264ms`
   - smart_construction_core provider screen then narrows the next target to
     `services/capability_registry.py:list_capabilities_for_user(...)`, with
     `resolve_capability_entry_target_payload(...)` as the highest-probability
     inner hotspot
   - smart_construction_core registry timing then confirms
     `resolve_capability_entry_target_payload(...)` dominates at about `7623ms`
   - scene-target timing then confirms repeated `resolve_scene_map` loading
     dominates that call at about `6740ms`, while xmlid resolution is only
     about `61ms`
   - scene-registry timing then confirms repeated
     `load_scene_registry_content_entries()` dominates that path at about
     `7587ms`, while DB scene fetch is only about `103ms`
   - content-loader timing then confirms the dominant sub-step is
     `scene_registry_engine.load_scene_registry_content_entries()` at about
     `4318ms`, with direct module exec a secondary cost at about `1339ms`
   - engine-loader timing then confirms that path is split between repeated
     `load_scene_provider_registry` at about `2425ms` and
     `resolve_scene_provider_path` at about `2228ms`
   - provider-registry timing then confirms `_resolve_addons_root(base_dir)`
     dominates that path at about `1949ms`, while registration work is
     negligible
   - resolve-addons-root screen then narrows the next concrete target to the
     `Path.resolve()` and parent-walk steps inside that helper
   - resolve-addons-root timing then confirms the real hotspot is two repeated
     `Path.resolve()` calls at about `860ms + 864ms`
2. then instrument and reduce `build_nav`
3. then instrument and reduce `build_scene_runtime_surface`

This is a scene-orchestration/runtime performance issue, not a business-fact
semantics issue.
