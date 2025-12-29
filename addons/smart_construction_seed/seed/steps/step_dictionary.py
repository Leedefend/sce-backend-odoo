# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Mark dictionary seed executed (placeholder for future dictionary creation)
    env["ir.config_parameter"].sudo().set_param("sc.seed.dictionary", "1")


register(
    SeedStep(
        name="dictionary",
        description="Seed base dictionaries (placeholder marker).",
        run=_run,
    )
)
