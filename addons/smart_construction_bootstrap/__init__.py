# -*- coding: utf-8 -*-
from . import hooks  # noqa: F401

# expose hook for Odoo loader
post_init_hook = hooks.post_init_hook
