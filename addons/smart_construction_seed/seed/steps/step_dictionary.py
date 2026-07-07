# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    # Scenario evidence marker; baseline dictionaries are created by dictionary_min.
    env["ir.config_parameter"].sudo().set_param("sc.seed.dictionary", "1")


register(
    SeedStep(
        name="dictionary",
        description="Record dictionary scenario evidence marker.",
        run=_run,
    )
)
