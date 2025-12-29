# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Bootstrap baseline settings for a fresh DB (idempotent)."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    ICP = env["ir.config_parameter"].sudo()
    lang = ICP.get_param("sc.bootstrap.lang", "zh_CN")
    tz = ICP.get_param("sc.bootstrap.tz", "Asia/Shanghai")
    cur = ICP.get_param("sc.bootstrap.currency", "CNY")

    # 1) Activate language (stable API)
    env["res.lang"]._activate_lang(lang)

    # 2) System defaults
    ICP.set_param("lang", lang)
    ICP.set_param("tz", tz)

    # 3) Company currency
    currency = env.ref(f"base.{cur}")
    env.company.write({"currency_id": currency.id})

    # 4) Admin user preferences
    admin = env.ref("base.user_admin")
    admin.write({"lang": lang, "tz": tz})

    _logger.info("Bootstrap baseline applied: lang=%s tz=%s currency=%s", lang, tz, cur)
