# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Placeholder marker for project skeleton seed
    env["ir.config_parameter"].sudo().set_param("sc.seed.project_skeleton", "1")


register(
    SeedStep(
        name="project_skeleton",
        description="Seed minimal project skeleton (placeholder marker).",
        run=_run,
    )
)
