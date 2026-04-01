# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _as_env(env_or_cr, registry=None):
    """Accept env (new API) or (cr, registry) signature and return Environment."""
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def post_init_hook(env_or_cr, registry=None):
    """Apply repeat-safe platform baseline defaults."""
    env = _as_env(env_or_cr, registry)

    icp = env["ir.config_parameter"].sudo()
    lang = icp.get_param("sc.bootstrap.lang", "zh_CN")
    tz = icp.get_param("sc.bootstrap.tz", "Asia/Shanghai")

    env["res.lang"]._activate_lang(lang)

    icp.set_param("lang", lang)
    icp.set_param("tz", tz)

    admin = env.ref("base.user_admin")
    admin.write({"lang": lang, "tz": tz})

    _logger.info("Platform bootstrap baseline applied: lang=%s tz=%s", lang, tz)
