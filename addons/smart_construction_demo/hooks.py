# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

def _ensure_env(cr_or_env):
    if isinstance(cr_or_env, api.Environment):
        return cr_or_env
    return api.Environment(cr_or_env, SUPERUSER_ID, {})

def pre_init_hook(cr_or_env):
    """
    BEFORE module data import: ensure baseline (taxes etc.) exists to avoid demo XML crash.
    """
    env = _ensure_env(cr_or_env)
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

def post_init_hook(env_or_cr, registry=None):
    """
    AFTER install: ensure taxes + normalize demo users.
    """
    env = _ensure_env(env_or_cr)
    ensure_demo_taxes(env)
    _normalize_demo_users_lang_tz(env)
