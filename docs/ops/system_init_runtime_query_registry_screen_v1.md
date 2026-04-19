# System Init Runtime Query Registry Screen v1

## Goal

Map the current top-level `system.init` residual around
`runtime_query_registry_build`, `load_capability_contributions`, and
`native_projection` to the smallest defensible next optimization target.

## Fixed Architecture Declaration

- Layer Target: Scene-orchestration layer diagnostics
- Module: runtime query registry outer-shell screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: scenario
- Reason: after payload-loop recovery, the dominant residual has moved outward
  to the runtime query registry build shell and native projection path

## Live Evidence Anchor

Current live ranking after payload-loop recovery:

- `prepare_runtime_context.load_capabilities_for_user`: about `1077ms`
- `capability_load.runtime_query_registry_build`: about `1020ms`
- `capability_load.runtime_query_registry.load_capability_contributions`: about `999ms`
- `capability_load.runtime_query_registry.load_capability_contributions.native_projection`: about `717ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension_loop_total`: about `179ms`
- `capability_load.runtime_query_registry.load_capability_contributions.extension.smart_construction_core.import_and_provider`: about `175ms`

This shows the dominant owner is now above the already-recovered
`smart_construction_core` payload loop.

## Code Mapping

### 1. Top wrapper

`addons/smart_core/core/capability_provider.py`

- `load_capabilities_for_user_with_timings(...)`
- stage: `runtime_query_registry_build`

This wrapper delegates to `CapabilityRegistryService.get_registry_bundle_with_timings(...)`
and then projects rows into the runtime list.

### 2. Registry build shell

`addons/smart_core/app_config_engine/capability/core/registry.py`

- `CapabilityRegistry.build_with_timings(...)`
- stage: `load_capability_contributions`

The registry build shell is mostly:

- `load_capability_contributions_with_timings(...)`
- `merge_capability_contributions(...)`
- `check_platform_owner_constraints(...)`
- `build_registry_snapshot(...)`

From the live ranking, the dominant part is `load_capability_contributions`,
not merge/freeze/ownership.

### 3. Native projection

`addons/smart_core/app_config_engine/capability/core/contribution_loader.py`

- `load_capability_contributions_with_timings(...)`
- stage: `native_projection`

This stage first calls:

- `load_native_capability_rows(env, user=user)`

before extension modules are processed.

### 4. Native projection fan-out

`addons/smart_core/app_config_engine/capability/native/native_projection_service.py`

`load_native_capability_rows(...)` sequentially executes:

- `project_menu_capabilities(...)`
- `project_window_action_capabilities(...)`
- `project_model_access_capabilities(...)`
- `project_server_action_capabilities(...)`
- `project_report_action_capabilities(...)`
- `project_view_binding_capabilities(...)`

### 5. Most likely dominant adapter

`addons/smart_core/app_config_engine/capability/native/model_adapter.py`

`project_model_access_capabilities(...)` is the heaviest-looking adapter by
structure because it:

- reads up to `4000` `ir.model` rows
- reads matching `ir.model.access` rows
- groups ACL rows by model
- computes user-visible permissions across that full set
- resolves XMLIDs for the model set

By comparison, the other adapters read much narrower slices:

- menus: limit `600`
- act_window: limit `600`
- server actions: limit `600`
- reports: limit `600`
- view bindings: limit `1200`

## Decision

The next optimization batch should not start from `runtime_query_registry_build`
as a whole.

The tighter and more defensible next target is:

- `native_projection`

and within it, the first bounded screen/optimization priority should be:

- `project_model_access_capabilities(...)`

## Non-Targets

The next batch should not reopen:

- smart_construction_core payload loop
- provider selection
- provider registration
- scene target payload cache

Those are no longer the outer owner.
