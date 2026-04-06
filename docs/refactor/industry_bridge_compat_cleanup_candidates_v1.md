# Industry Bridge Compatibility Cleanup Candidates v1

## Scope

Target module: `addons/smart_construction_core/core_extension.py`

Residual compatibility exports (`def smart_core_*`) screened after ownership
migration batches 1067-1075.

## Candidate Matrix

- `smart_core_register`
  - status: compatibility wrapper
  - platform primary path: `get_intent_handler_contributions` + smart_core loader
  - cleanup priority: P1
  - removal precondition: all extension modules migrated to contribution hook

- `smart_core_list_capabilities_for_user` / `smart_core_capability_groups`
  - status: legacy fallback provider
  - platform primary path: `capability_contribution_loader`
  - cleanup priority: P1
  - removal precondition: industry module exposes `get_capability_contributions` hooks

- `smart_core_scene_package_service_class` / `smart_core_scene_governance_service_class`
  - status: legacy fallback provider
  - platform primary path: direct import in smart_core handlers
  - cleanup priority: P0
  - removal precondition: no runtime fallback hits in target environments

- `smart_core_load_scene_configs` / `smart_core_has_db_scenes` / `smart_core_get_scene_version` / `smart_core_get_schema_version`
  - status: legacy fallback provider
  - platform primary path: direct import in `scene_registry_provider`
  - cleanup priority: P0
  - removal precondition: direct import path stable across rollout dbs

- `smart_core_server_action_window_map`
  - status: legacy policy override
  - platform primary path: `smart_core.core.platform_policy_defaults`
  - cleanup priority: P1
  - removal precondition: policy contributions migrated to `get_server_action_window_map_contributions`

- `smart_core_file_upload_allowed_models` / `smart_core_file_download_allowed_models`
  - status: legacy policy override
  - platform primary path: `platform_policy_defaults`
  - cleanup priority: P1
  - removal precondition: modules use `get_file_*_allowed_model_contributions`

- `smart_core_api_data_write_allowlist` / `smart_core_api_data_unlink_allowed_models`
  - status: legacy policy override
  - platform primary path: `platform_policy_defaults`
  - cleanup priority: P1
  - removal precondition: modules use `get_api_data_*_contributions`

- `smart_core_model_code_mapping`
  - status: legacy policy override
  - platform primary path: `platform_policy_defaults`
  - cleanup priority: P1
  - removal precondition: modules use `get_model_code_mapping_contributions`

- `smart_core_create_field_fallbacks`
  - status: legacy contribution hook
  - platform primary path: `get_create_field_fallback_contributions` via `platform_policy_defaults`
  - cleanup priority: P2
  - removal precondition: contribution hook migration completed for dependent modules

- `smart_core_extend_system_init`
  - status: legacy compatibility wrapper
  - platform primary path: `get_system_init_fact_contributions` + `apply_extension_fact_contributions`
  - cleanup priority: P1
  - removal precondition: all active extensions migrated to contribution hook

## Proposed Deletion Order

1. P0 scene bridge legacy exports
2. P1 intent/system_init/policy legacy exports
3. P2 create fallback legacy export

## Risk Notes

- direct deletion without fallback-usage evidence can break external extension modules.
- next implementation batch should include bounded runtime grep/assert for remaining legacy hook callers.

