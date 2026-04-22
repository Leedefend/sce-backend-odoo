# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import services
from . import wizard
from .hooks import pre_init_hook, post_init_hook, ensure_core_taxes
from . import core_extension

# expose extension hooks for smart_core extension loader
from .core_extension import (  # noqa: F401
    get_intent_handler_contributions,
    get_system_init_fact_contributions,
    get_capability_contributions,
    get_capability_group_contributions,
    get_server_action_window_map_contributions,
    get_file_upload_allowed_model_contributions,
    get_file_download_allowed_model_contributions,
    get_api_data_write_allowlist_contributions,
    get_api_data_unlink_allowed_model_contributions,
    get_model_code_mapping_contributions,
    get_create_field_fallback_contributions,
    smart_core_extend_system_init,
    smart_core_identity_profile,
    smart_core_nav_scene_maps,
    smart_core_critical_scene_target_overrides,
    smart_core_critical_scene_target_route_overrides,
    smart_core_build_portal_dashboard,
    smart_core_build_capability_matrix,
    smart_core_get_project_insight,
    smart_core_build_portal_execute_button_contract,
    smart_core_build_project_execution_service,
    smart_core_build_project_dashboard_service,
    smart_core_build_project_plan_bootstrap_service,
    smart_core_build_cost_tracking_service,
    smart_core_build_payment_slice_service,
    smart_core_build_settlement_slice_service,
)
