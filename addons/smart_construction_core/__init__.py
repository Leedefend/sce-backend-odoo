# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import services
from . import wizard
from .hooks import pre_init_hook, post_init_hook, ensure_core_taxes
from . import core_extension

# expose extension hooks for smart_core extension loader
from .core_extension import smart_core_register, smart_core_extend_system_init  # noqa: F401
