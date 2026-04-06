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
    get_create_field_fallback_contributions,
)
