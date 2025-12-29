# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Placeholder metrics marker
    env["ir.config_parameter"].sudo().set_param("sc.seed.metrics_smoke", "1")


register(
    SeedStep(
        name="metrics_smoke",
        description="Seed minimal metrics evidence (placeholder marker).",
        run=_run,
    )
)
