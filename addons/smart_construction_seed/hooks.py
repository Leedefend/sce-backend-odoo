# -*- coding: utf-8 -*-
import logging
import os

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Seed placeholder hook (idempotent). Extend with real seed data later."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    ICP = env["ir.config_parameter"].sudo()

    env_seed_enabled = os.getenv("SC_SEED_ENABLED")
    env_mode = os.getenv("SC_BOOTSTRAP_MODE")

    mode = env_mode or ICP.get_param("sc.bootstrap.mode", "prod")
    seed_enabled = env_seed_enabled if env_seed_enabled is not None else ICP.get_param("sc.bootstrap.seed_enabled", "0")

    if seed_enabled != "1":
        _logger.info("Seed skipped: sc.bootstrap.seed_enabled=%s mode=%s", seed_enabled, mode)
        return

    _logger.info("Seed hook executed (mode=%s). Extend with seed data as needed.", mode)
