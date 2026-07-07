# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Scenario evidence marker for metrics coverage.
    env["ir.config_parameter"].sudo().set_param("sc.seed.metrics_smoke", "1")


register(
    SeedStep(
        name="metrics_smoke",
        description="Record metrics scenario evidence marker.",
        run=_run,
    )
)
