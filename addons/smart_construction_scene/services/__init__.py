# -*- coding: utf-8 -*-
from . import capability_scene_targets  # noqa: F401
from . import my_work_scene_targets  # noqa: F401
from . import project_management_entry_target  # noqa: F401

try:
    from . import scene_governance_service  # noqa: F401
    from . import scene_package_service  # noqa: F401
except (ImportError, ModuleNotFoundError) as exc:
    message = str(exc)
    if "odoo" not in message and getattr(exc, "name", "") != "odoo":
        raise
