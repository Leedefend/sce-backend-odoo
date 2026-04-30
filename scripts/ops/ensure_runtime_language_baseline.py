# -*- coding: utf-8 -*-
"""Ensure deterministic runtime language baseline for rebuilt databases.

Run through Odoo shell:
    DB_NAME=sc_prod_sim make runtime.language.ensure
"""

import os


LANG_CODE = os.getenv("SC_RUNTIME_LANG", "zh_CN").strip() or "zh_CN"
TZ = os.getenv("SC_RUNTIME_TZ", "Asia/Shanghai").strip() or "Asia/Shanghai"
OVERWRITE = os.getenv("SC_RUNTIME_LANG_OVERWRITE", "1").strip().lower() not in {"0", "false", "no"}


def _ensure_language_loaded(env, code):
    Lang = env["res.lang"].sudo().with_context(active_test=False)
    lang = Lang.search([("code", "=", code)], limit=1)
    if not lang:
        raise RuntimeError(
            "%s language record is missing; install modules with --load-language=%s before baseline"
            % (code, code)
        )
    if not lang.active:
        lang.write({"active": True})

    wizard = env["base.language.install"].sudo().create(
        {
            "lang_ids": [(6, 0, [lang.id])],
            "overwrite": bool(OVERWRITE),
        }
    )
    wizard.lang_install()
    return lang


def _normalize_users(env, lang_code, tz):
    Users = env["res.users"].sudo().with_context(active_test=False)
    users = Users.search([])
    updated = 0
    for user in users:
        vals = {}
        if user.lang != lang_code:
            vals["lang"] = lang_code
        if tz and user.tz != tz:
            vals["tz"] = tz
        if vals:
            user.write(vals)
            updated += 1
    partners = users.mapped("partner_id").filtered(lambda partner: partner)
    if partners:
        partners.write({"lang": lang_code, "tz": tz})
    return len(users), updated


def _set_params(env, lang_code, tz):
    icp = env["ir.config_parameter"].sudo()
    for key in ("sc.bootstrap.lang", "sc.platform.default_lang", "sc.runtime.default_lang"):
        icp.set_param(key, lang_code)
    for key in ("sc.bootstrap.tz", "sc.platform.default_tz", "sc.runtime.default_tz"):
        icp.set_param(key, tz)


lang = _ensure_language_loaded(env, LANG_CODE)
user_count, updated_count = _normalize_users(env, lang.code, TZ)
_set_params(env, lang.code, TZ)
env.cr.commit()

print(
    {
        "status": "PASS",
        "lang": lang.code,
        "lang_active": bool(lang.active),
        "tz": TZ,
        "users": user_count,
        "users_updated": updated_count,
        "translations_overwrite": bool(OVERWRITE),
    }
)
