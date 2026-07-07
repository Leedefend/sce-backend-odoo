# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Scenario evidence marker for project skeleton coverage.
    env["ir.config_parameter"].sudo().set_param("sc.seed.project_skeleton", "1")


register(
    SeedStep(
        name="project_skeleton",
        description="Record project skeleton scenario evidence marker.",
        run=_run,
    )
)
