# -*- coding: utf-8 -*-
from . import hooks

# Keep hook entrypoints visible for manifest references
from .hooks import ensure_demo_taxes, pre_init_hook  # noqa: F401

# post_init_hook may or may not exist depending on branch history
try:
    from .hooks import post_init_hook  # noqa: F401
except Exception:
    post_init_hook = None  # noqa: F401
