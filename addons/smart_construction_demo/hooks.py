# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api
from odoo.addons.smart_construction_core import hooks as core_hooks


def ensure_demo_taxes(env_or_cr, registry=None):
    """Delegate to core hook to ensure default taxes are present/bound.

    This keeps demo/CI reproducible without letting the core module seed taxes.
    """
    if registry:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    else:
        env = env_or_cr
    core_hooks.ensure_core_taxes(env)
