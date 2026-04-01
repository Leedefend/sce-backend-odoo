# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _as_env(env_or_cr, registry=None):
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def post_init_hook(env_or_cr, registry=None):
    """Apply fresh-DB currency compatibility for legacy bootstrap flows."""
    env = _as_env(env_or_cr, registry)

    icp = env["ir.config_parameter"].sudo()
    cur = icp.get_param("sc.bootstrap.currency", "CNY")
    currency = env.ref(f"base.{cur}")
    env.company.write({"currency_id": currency.id})

    _logger.info("Construction bootstrap compatibility applied: currency=%s", cur)
