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


DEMO_LOGINS = [
    "demo_pm",
    "demo_finance",
    "demo_cost",
    "demo_audit",
    "demo_readonly",
]


def post_init_hook(cr, registry):
    """Normalize demo users' language/timezone for trial UX."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    users = env["res.users"].search([("login", "in", DEMO_LOGINS)])
    if users:
        to_write = users.filtered(
            lambda u: (u.lang or "") != "zh_CN" or (u.tz or "") != "Asia/Shanghai"
        )
        if to_write:
            to_write.write({"lang": "zh_CN", "tz": "Asia/Shanghai"})
    ensure_demo_taxes(cr, registry)
