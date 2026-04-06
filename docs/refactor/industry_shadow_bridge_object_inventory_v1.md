# Industry Shadow Bridge Object Inventory v1

## Inventory Matrix

| object | current owner | target owner | priority | migration approach |
| --- | --- | --- | --- | --- |
| `smart_core_register` | `smart_construction_core` | `smart_core` registry final-owner (industry as contribution provider) | P0 | replace registry write with `get_intent_handler_contributions()` |
| `smart_core_list_capabilities_for_user` | `smart_construction_core` | `smart_core` capability runtime/projection owner | P0 | migrate to platform capability query service |
| `smart_core_capability_groups` | `smart_construction_core` | `smart_core` capability projection owner | P0 | convert to capability-group contributions |
| `smart_core_scene_package_service_class` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy, platform direct scene access |
| `smart_core_scene_governance_service_class` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy, platform direct scene access |
| `smart_core_load_scene_configs` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy call path |
| `smart_core_has_db_scenes` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy call path |
| `smart_core_get_scene_version` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy call path |
| `smart_core_get_schema_version` | `smart_construction_core` bridge | scene/platform formal interface | P0 | remove industry proxy call path |
| `smart_core_server_action_window_map` | industry constant owner | platform policy/config owner | P1 | move to platform policy + optional contribution overlay |
| `smart_core_file_upload_allowed_models` | industry constant owner | platform file policy owner | P1 | migrate to platform file policy host |
| `smart_core_file_download_allowed_models` | industry constant owner | platform file policy owner | P1 | migrate to platform file policy host |
| `smart_core_api_data_write_allowlist` | industry constant owner | platform data-api policy owner | P1 | move to platform policy layer |
| `smart_core_api_data_unlink_allowed_models` | industry constant owner | platform data-api policy owner | P1 | move to platform policy layer |
| `smart_core_model_code_mapping` | industry constant owner | platform model exposure policy owner | P1 | migrate to platform exposure registry |
| `smart_core_create_field_fallbacks` | industry pseudo-platform owner | platform contribution consumer (industry contribution) | P1 | rename to contribution provider and platform merge |
| `smart_core_extend_system_init` | industry startup assembler | platform system.init owner (industry ext_facts provider) | P1 | split into fact providers + platform merge |

## Batch-0 Freeze Confirmation

- no new `smart_core_*` bridge functions are allowed.
- no new industry direct registry write pattern is allowed.
- no new platform policy constant ownership is allowed in industry modules.

