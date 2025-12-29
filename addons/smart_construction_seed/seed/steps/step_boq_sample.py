# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Placeholder for BOQ sample seed, record intended count
    env["ir.config_parameter"].sudo().set_param("sc.seed.boq_count", "10")


register(
    SeedStep(
        name="boq_sample",
        description="Seed sample BOQ entries (placeholder marker).",
        run=_run,
    )
)
