# -*- coding: utf-8 -*-

from . import core_extension  # noqa: F401
from .core_extension import (  # noqa: F401
    get_intent_handler_contributions,
    get_system_init_fact_contributions,
    smart_core_resolve_startup_delivery_identity,
    smart_core_extend_system_init,
)
from .hooks import post_init_hook
