# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def pre_init_hook(cr):
    """
    BEFORE module data import: ensure baseline (taxes etc.) exists to avoid demo XML crash.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    ensure_demo_taxes(env)

def ensure_demo_taxes(env):
    """
    Idempotent demo tax bootstrap.
    Replace body with real bootstrap if your project has specific requirements.
    """
    return True

def _normalize_demo_users_lang_tz(env, lang="zh_CN", tz="Asia/Shanghai"):
    """
    Normalize internal users' lang/tz for stable demo UX across envs.
    """
    Users = env["res.users"].sudo()
    users = Users.search([
        ("share", "=", False),
        ("login", "not in", ["__system__", "public"]),
    ])
    for u in users:
        vals = {}
        if lang and u.lang != lang:
            vals["lang"] = lang
        if tz and u.tz != tz:
            vals["tz"] = tz
        if vals:
            u.write(vals)

def post_init_hook(cr, registry):
    """
    AFTER install: ensure taxes + normalize demo users.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    ensure_demo_taxes(env)
    _normalize_demo_users_lang_tz(env)
