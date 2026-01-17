# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _set_default_param(params, key, value):
    current = params.get_param(key, default=None)
    if current is None or current == "":
        params.set_param(key, value)


def _run(env):
    params = env["ir.config_parameter"].sudo()
    params.set_param("sc.login.env", "prod")
    _set_default_param(params, "sc.login.custom_enabled", "1")
    _set_default_param(params, "sc.workbench.enabled", "1")
    _set_default_param(
        params,
        "sc.workbench.default_action_xmlid",
        "smart_construction_core.action_sc_project_workbench",
    )
    _set_default_param(params, "sc.sidebar.overview_enabled", "1")
    _set_default_param(params, "sc.sidebar.overview_menu_ids", "265")


register(
    SeedStep(
        name="icp_defaults",
        description="Seed minimal ICP defaults for login/workbench/sidebar.",
        run=_run,
    )
)
