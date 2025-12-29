# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    env["ir.config_parameter"].sudo().set_param("sc.seed.sanity_ran", "1")


register(
    SeedStep(
        name="sanity",
        description="Minimal no-op step to validate seed pipeline",
        run=_run,
    )
)
