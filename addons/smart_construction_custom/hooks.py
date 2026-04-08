# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


def _as_env(env_or_cr, registry=None):
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def _apply_user_locale_baseline(env, lang="zh_CN", tz="Asia/Shanghai"):
    env["res.lang"]._activate_lang(lang)
    icp = env["ir.config_parameter"].sudo()
    icp.set_param("lang", lang)
    icp.set_param("tz", tz)

    users = env["res.users"].sudo().search([
        ("share", "=", False),
        ("active", "=", True),
    ])
    for user in users:
        vals = {}
        if user.lang != lang:
            vals["lang"] = lang
        if (user.tz or "") != tz:
            vals["tz"] = tz
        if vals:
            user.write(vals)


def _ensure_language_pack_loaded(env, lang="zh_CN"):
    language = env["res.lang"].search([("code", "=", lang)], limit=1)
    if not language:
        return

    needs_install = True
    settings_menu = env.ref("base.menu_administration", raise_if_not_found=False)
    if settings_menu:
        env.cr.execute("SELECT name FROM ir_ui_menu WHERE id = %s", (settings_menu.id,))
        row = env.cr.fetchone()
        if row and isinstance(row[0], dict) and lang in row[0]:
            needs_install = False

    if not needs_install:
        return

    wizard = env["base.language.install"].create(
        {
            "lang_ids": [(6, 0, [language.id])],
            "overwrite": True,
        }
    )
    wizard.lang_install()


def apply_business_full_policy(env):
    env["sc.security.policy"].apply_business_full_policy()


def post_init_hook(env_or_cr, registry=None):
    env = _as_env(env_or_cr, registry)
    _ensure_language_pack_loaded(env)
    _apply_user_locale_baseline(env)
    apply_business_full_policy(env)
