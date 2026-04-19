# System Init Capability Load Screen v1

## Goal

Screen the real ownership inside `_load_capabilities_for_user(...)` before
opening a capability-provider optimization batch.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: `system.init` capability-loading ownership screen
- Module Ownership: existing backend code inspection + docs
- Kernel or Scenario: scenario
- Reason: the previous timing batch proved capability loading dominates startup
  runtime, so the next batch must target a concrete capability-provider
  sub-step rather than the whole path

## Inherited Facts

- `prepare_runtime_context`: about `7987ms`
- `load_capabilities_for_user`: about `7821ms`
- `normalize_capabilities`: about `25ms`
- `build_base_call`: `0ms`

## Code-Inspection Result

`load_capabilities_for_user(...)` is a thin orchestrator with three possible
branches:

1. runtime capability query path
   - `CapabilityQueryService.list_capabilities_for_user(...)`
   - delegates to `CapabilityRegistryService.get_registry_bundle(...)`
   - delegates to `CapabilityRegistry.build(...)`
2. extension contribution fallback path
   - `collect_capability_contributions(env, user)`
3. model fallback path
   - `env["sc.capability"].search(...)` plus `_user_visible()` /
     `to_public_dict()`

Further inspection shows:

- `CapabilityQueryService.list_capabilities_for_user(...)` is a thin facade
- `CapabilityRegistryService.get_registry_bundle(...)` is a thin facade
- `CapabilityRegistry.build(...)` is also a thin orchestrator over:
  - `load_capability_contributions(...)`
  - `merge_capability_contributions(...)`
  - `check_platform_owner_constraints(...)`
  - `build_registry_snapshot(...)`

Within `load_capability_contributions(...)`, the candidate cost centers are:

1. `load_native_capability_rows(env, user=user)`
   - internally fans out to native adapters:
     - menu
     - window action
     - model access
     - server action
     - report action
     - view binding
2. `validate_and_normalize_rows(native_rows, source_module="smart_core.native")`
3. extension module enumeration via `iter_extension_modules(env)`
4. per-extension module import and `get_capability_contributions(...)`
5. per-extension `validate_and_normalize_rows(...)`

By contrast, the following code paths look structurally cheap and are unlikely
to explain a `7.8s` hotspot on their own:

- `merge_capability_contributions(...)`
- `build_registry_snapshot(...)`
- the thin query/registry service wrappers

## Ownership Decision

The next runtime implementation batch should instrument the capability-loading
path at this lower layer:

1. native capability row projection
2. native schema normalize/validate
3. extension module enumeration/import/provider loop
4. contribution merge
5. registry snapshot build

The highest-probability hotspot is the native projection path, not the final
merge/snapshot layer.

## Follow-up Timing Result

The follow-up instrumentation batch has now proven the first split inside
capability loading:

- `capability_load.runtime_query_service`: about `7285ms`
- `prepare_runtime_context.load_capabilities_for_user`: about `7286ms`
- no fallback-stage timings were hit in the real `wutao / sc_demo` probe

### Updated Ownership Decision

The active runtime path is the query/registry branch, not fallback behavior.

The next instrumentation batch should move one layer deeper into:

1. `CapabilityRegistry.build(...)`
2. `load_capability_contributions(...)`
3. then native projection vs schema normalize vs extension loop

## Runtime Query Split Result

The next instrumentation batch has now split the active runtime-query branch:

- `runtime_query_registry_build`: about `8417ms`
- `runtime_query_registry.load_capability_contributions`: about `8411ms`
- `runtime_query_registry.merge_capability_contributions`: about `2ms`
- `runtime_query_registry.check_platform_owner_constraints`: about `1ms`
- `runtime_query_registry.build_registry_snapshot`: about `1ms`
- `runtime_query_list_projection`: about `10ms`

### Updated Ownership Decision

The real hotspot is now assigned to `load_capability_contributions(...)`.

The next batch should instrument only this lower layer:

1. `load_native_capability_rows(...)`
2. native `validate_and_normalize_rows(...)`
3. extension module enumeration/import/provider loop
4. per-extension `validate_and_normalize_rows(...)`

## Contribution Load Split Result

The next instrumentation batch has now split `load_capability_contributions(...)`:

- `runtime_query_registry.load_capability_contributions`: about `8340ms`
- `runtime_query_registry.load_capability_contributions.extension_loop_total`: about `8046ms`
- `runtime_query_registry.load_capability_contributions.extension.smart_construction_core.import_and_provider`: about `8043ms`
- `runtime_query_registry.load_capability_contributions.native_projection`: about `264ms`
- `runtime_query_registry.load_capability_contributions.native_schema_normalize`: about `27ms`
- other extension import/provider stages were effectively `0ms` in the current probe

### Updated Ownership Decision

The real hotspot is now assigned to the extension provider path of
`smart_construction_core`, not native projection and not schema normalize.

The next batch should inspect and instrument:

1. `smart_construction_core.get_capability_contributions(...)`
2. any lower provider/query path it delegates to

Code inspection has now narrowed that lower path further:

- `core_extension.get_capability_contributions(...)` is only a wrapper
- the next concrete target is
  `smart_construction_core.services.capability_registry.list_capabilities_for_user(...)`
- the highest-probability hotspot inside that function is
  `resolve_capability_entry_target_payload(...)` in the per-capability loop

Follow-up timing has now confirmed that hypothesis:

- `smart_construction_core.provider.loop_resolve_capability_entry_target_payload`: about `7623ms`
- other inner provider stages are negligible by comparison
- lower scene-target timing then confirms the real cost inside that call is
  repeated `resolve_scene_map` loading at about `6740ms`, not xmlid resolution
- scene-registry timing then proves the real cost inside scene-map loading is
  repeated `load_scene_registry_content_entries()` at about `7587ms`, not DB
  scene fetch or merge logic
- content-loader timing then proves the dominant sub-step is the scene registry
  engine loader call at about `4318ms`, with direct module exec a secondary
  cost at about `1339ms`
- engine-loader timing then proves that cost is split between repeated
  `load_scene_provider_registry` at about `2425ms` and
  `resolve_scene_provider_path` at about `2228ms`
- provider-registry timing then proves the real hotspot inside that path is
  `_resolve_addons_root(base_dir)` at about `1949ms`, not provider
  registration
- resolve-addons-root screen then narrows the likely cost to repeated
  `Path.resolve()` and parent-chain materialization on the mounted workspace path
- resolve-addons-root timing then confirms the real cost is the two repeated
  `Path.resolve()` calls, not parent walking
