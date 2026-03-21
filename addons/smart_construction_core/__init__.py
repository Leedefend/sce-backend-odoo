# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import services
from . import wizard
from .hooks import pre_init_hook, post_init_hook, ensure_core_taxes
from . import core_extension

# expose extension hooks for smart_core extension loader
from .core_extension import (  # noqa: F401
    smart_core_register,
    smart_core_extend_system_init,
    smart_core_identity_profile,
    smart_core_list_capabilities_for_user,
    smart_core_capability_groups,
    smart_core_nav_scene_maps,
    smart_core_scene_package_service_class,
    smart_core_scene_governance_service_class,
    smart_core_load_scene_configs,
    smart_core_has_db_scenes,
    smart_core_get_scene_version,
    smart_core_get_schema_version,
    smart_core_server_action_window_map,
    smart_core_critical_scene_target_overrides,
    smart_core_critical_scene_target_route_overrides,
    smart_core_file_upload_allowed_models,
    smart_core_file_download_allowed_models,
    smart_core_api_data_write_allowlist,
    smart_core_api_data_unlink_allowed_models,
    smart_core_model_code_mapping,
    smart_core_create_field_fallbacks,
    smart_core_surface_nav_allowlist,
    smart_core_surface_deep_link_allowlist,
    smart_core_surface_policy_default_name,
    smart_core_surface_policy_file_default,
)
