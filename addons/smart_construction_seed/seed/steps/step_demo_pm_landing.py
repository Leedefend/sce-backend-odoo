# -*- coding: utf-8 -*-
import logging

from ..registry import SeedStep, register

_logger = logging.getLogger(__name__)


def _run(env):
    user = env.ref("smart_construction_demo.sc_demo_user_pm", raise_if_not_found=False)
    action = env.ref("smart_construction_core.action_sc_project_list", raise_if_not_found=False)
    if not user or not action:
        _logger.info("demo_pm landing skipped: user or action missing")
        return
    if user.action_id != action:
        user.sudo().write({"action_id": action.id})


register(
    SeedStep(
        name="demo_pm_landing",
        description="Set demo PM landing action to project list",
        run=_run,
    )
)
