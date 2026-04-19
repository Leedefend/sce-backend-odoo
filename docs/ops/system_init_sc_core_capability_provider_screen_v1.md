# System Init smart_construction_core Capability Provider Screen v1

## Goal

Screen the real ownership inside `smart_construction_core` capability
contributions before opening the next instrumentation batch.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: `smart_construction_core` capability provider ownership screen
- Module Ownership: existing backend code inspection + docs
- Kernel or Scenario: scenario
- Reason: the previous timing batch proved
  `extension.smart_construction_core.import_and_provider` dominates contribution
  loading, so the next batch must target a concrete inner sub-step

## Inherited Facts

- `extension.smart_construction_core.import_and_provider`: about `8043ms`
- native capability projection path is only about `264ms`
- native schema normalize is only about `27ms`

## Code-Inspection Result

`addons/smart_construction_core/core_extension.py:get_capability_contributions()`
is only a wrapper:

1. import `services.capability_registry.list_capabilities_for_user`
2. call it
3. map returned rows into contribution contract shape

The likely hotspot therefore sits inside:

- `addons/smart_construction_core/services/capability_registry.py:list_capabilities_for_user(...)`

Within that function:

1. `capability_definitions()` is a static in-memory list builder
2. `_resolve_role_codes_for_user(user)` runs once
3. the main per-capability loop performs:
   - `_capability_access(...)`
   - `_capability_state(...)`
   - `build_capability_entry_target(...)`
   - `resolve_capability_entry_target_payload(env, capability_key, explicit_target=...)`
4. results are appended and finally sorted

## Ownership Decision

The next instrumentation batch should not target `core_extension` wrapper code.

The next concrete target should be inside
`services/capability_registry.py:list_capabilities_for_user(...)`, with
separate timings for:

1. role-code resolution
2. static capability definition materialization
3. per-capability access/state checks
4. `build_capability_entry_target(...)`
5. `resolve_capability_entry_target_payload(...)`
6. final sort

The highest-probability hotspot is `resolve_capability_entry_target_payload(...)`
inside the per-capability loop.

## Follow-up Timing Result

The follow-up instrumentation batch has now split the inner provider loop:

- `provider.loop_resolve_capability_entry_target_payload`: about `7623ms`
- `provider.resolve_role_codes_for_user`: about `12ms`
- `provider.loop_access_and_state`: about `2ms`
- `provider.loop_build_capability_entry_target`: `0ms`
- `provider.capability_definitions`: `0ms`
- `provider.group_meta_map`: `0ms`
- `provider.final_sort`: `0ms`

### Updated Ownership Decision

The real hotspot inside smart_construction_core capability provider is now
assigned precisely to:

- `resolve_capability_entry_target_payload(...)`

The next batch should inspect and instrument that function and the lower scene
target resolution path it delegates to.

## Scene Target Split Result

The next instrumentation batch has now split
`resolve_capability_entry_target_payload(...)`:

- `payload.resolve_scene_map`: about `6740ms`
- `payload.resolve_xmlids`: about `61ms`
- `payload.build_capability_entry_target`: `0ms`
- `payload.overlay_explicit_target`: `0ms`

### Updated Ownership Decision

The real hotspot is now assigned to repeated scene map loading:

- `_resolve_scene_map(env)` -> `scene_registry.load_scene_configs(env)`

The next batch should inspect and instrument `scene_registry.load_scene_configs`
instead of capability provider wrappers.

## Scene Registry Split Result

The next instrumentation batch has now split `scene_registry.load_scene_configs`:

- `scene_registry.load_scene_registry_content_entries`: about `7587ms`
- `scene_registry.load_from_db`: about `103ms`
- `scene_registry.load_imported_scenes`: about `1ms`
- `scene_registry.include_test_scenes`: about `1ms`
- merge/filter/build-maps stages are effectively `0ms`

### Updated Ownership Decision

The real hotspot is now assigned to repeated registry-content loading:

- `_load_scene_registry_content_entries()`

The next batch should inspect and instrument that loader path rather than DB
scene loading or merge logic.

## Registry Content Loader Split Result

The next instrumentation batch has now split
`_load_scene_registry_content_entries()`:

- `content_entries.engine_loader_call`: about `4318ms`
- `content_entries.direct_module_exec`: about `1339ms`
- `content_entries.load_scene_registry_engine_module`: about `54ms`
- `content_entries.direct_module_spec`: `0ms`
- `content_entries.direct_list_scene_entries`: `0ms`

### Updated Ownership Decision

The real hotspot is now assigned to the scene registry engine loader path,
especially:

- `smart_scene/core/scene_registry_engine.py:load_scene_registry_content_entries()`

The next batch should inspect and instrument that engine loader path before
considering direct module execution optimizations.

## Engine Loader Split Result

The next instrumentation batch has now split the engine loader:

- `engine.load_scene_provider_registry`: about `2425ms`
- `engine.resolve_scene_provider_path`: about `2228ms`

### Updated Ownership Decision

The engine hotspot is split across two repeated dynamic operations:

1. loading `scene_provider_registry.py`
2. resolving the provider path via provider-registry rebuild

The next batch should inspect and instrument
`smart_scene/core/scene_provider_registry.py`.

Code inspection has now narrowed that next target further:

- `_resolve_addons_root(base_dir)` is dominated by path-resolution mechanics
- the highest-probability hotspot is the first `base_dir.resolve()` on the
  mounted workspace path

## Provider Registry Split Result

The next instrumentation batch has now split the provider-registry path:

- `resolve.build_scene_provider_registry`: about `1996ms`
- `resolve.registry.resolve_addons_root`: about `1949ms`
- `resolve.registry.register_fallback_providers`: about `16ms`
- `resolve.registry.register_from_modules`: `0ms`
- `resolve.registry_get_provider`: `0ms`

### Updated Ownership Decision

The real provider-registry hotspot is now assigned to:

- `_resolve_addons_root(base_dir)`

The next batch should inspect and instrument that path-resolution helper before
touching registry registration logic.

Follow-up timing has now confirmed the exact hotspot shape:

- `_resolve_addons_root.base_dir_resolve`: about `860ms`
- `_resolve_addons_root.fallback_second_resolve`: about `864ms`
- parent-chain work is negligible

## Redundant Resolve Optimization Result

The follow-up low-risk optimization removed the redundant fallback
`base_dir.resolve()` call and reused the already-resolved `current` path for
the final fallback branch.

Real probe results after the change:

- `resolve.build_scene_provider_registry`: about `1204ms`
- `resolve_scene_provider_path`: about `1206ms`
- `_resolve_addons_root.base_dir_resolve`: about `855ms`
- `_resolve_addons_root.fallback_second_resolve`: `0ms`

### Updated Ownership Decision

The provider-registry path has already recovered roughly `800ms` by removing
the second resolve call. The remaining dominant cost is now the first
`base_dir.resolve()` on the mounted workspace path, so any next batch should
target that single residual filesystem-resolution hotspot rather than registry
registration logic.
