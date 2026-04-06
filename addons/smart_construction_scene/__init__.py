# -*- coding: utf-8 -*-
from . import scene_registry  # noqa: F401

from . import models  # noqa: F401
from . import core_extension  # noqa: F401

from .core_extension import (  # noqa: F401
    get_intent_handler_contributions,
    smart_core_extend_system_init,
    smart_core_identity_profile,
    smart_core_nav_scene_maps,
    smart_core_surface_nav_allowlist,
    smart_core_surface_deep_link_allowlist,
    smart_core_surface_policy_default_name,
    smart_core_surface_policy_file_default,
    smart_core_critical_scene_target_overrides,
    smart_core_critical_scene_target_route_overrides,
)
