# -*- coding: utf-8 -*-
import logging
import os

from odoo import SUPERUSER_ID, api, fields

from .seed import run_steps

_logger = logging.getLogger(__name__)


def _as_env(env_or_cr, registry=None):
    if isinstance(env_or_cr, api.Environment):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def post_init_hook(env_or_cr, registry=None):
    """Seed placeholder hook (idempotent). Extend with real seed data later."""
    env = _as_env(env_or_cr, registry)
    ICP = env["ir.config_parameter"].sudo()

    env_seed_enabled = os.getenv("SC_SEED_ENABLED")
    env_mode = os.getenv("SC_BOOTSTRAP_MODE")
    env_steps = os.getenv("SC_SEED_STEPS")
    env_profile = os.getenv("SC_SEED_PROFILE")

    mode = env_mode or ICP.get_param("sc.bootstrap.mode", "prod")
    seed_enabled = env_seed_enabled if env_seed_enabled is not None else ICP.get_param("sc.bootstrap.seed_enabled", "0")
    enabled = seed_enabled in ("1", "true", "True")
    profile = env_profile if env_profile is not None else ICP.get_param("sc.seed.profile", "")
    steps_sel = env_steps if env_steps is not None else ICP.get_param("sc.seed.steps", "all")
    if profile:
        steps_sel = f"profile:{profile}"

    if not enabled:
        _logger.info("Seed skipped: sc.bootstrap.seed_enabled=%s mode=%s", seed_enabled, mode)
        return

    if mode == "demo":
        ICP.set_param("sc.login.env", "demo")
        ICP.set_param("sc.login.custom_enabled", "1")
        demo_user = env.ref("smart_construction_demo.sc_demo_user_pm", raise_if_not_found=False)
        demo_action = env.ref("project.open_view_project_all", raise_if_not_found=False)
        if demo_user and demo_action and demo_user.action_id != demo_action:
            demo_user.sudo().write({"action_id": demo_action.id})

    executed = run_steps(env, steps_sel)

    # mark execution evidence for verify/demo
    ICP.set_param("sc.seed.enabled", "1")
    ICP.set_param("sc.seed.mode", mode)
    ICP.set_param("sc.seed.last_steps", ",".join(executed))
    ICP.set_param("sc.seed.ran_at", fields.Datetime.now().isoformat())

    _logger.info("Seed hook executed (mode=%s steps=%s). Extend with seed data as needed.", mode, executed)
