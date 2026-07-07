# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Scenario evidence marker for expected BOQ coverage.
    env["ir.config_parameter"].sudo().set_param("sc.seed.boq_count", "10")


register(
    SeedStep(
        name="boq_sample",
        description="Record BOQ scenario evidence marker.",
        run=_run,
    )
)
