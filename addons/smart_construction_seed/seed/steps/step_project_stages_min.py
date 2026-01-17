# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _ensure_stage(env, name, sequence, *, is_default=False, fold=False):
    Stage = env["project.project.stage"].sudo().with_context(active_test=False)
    stage = Stage.search([("name", "=", name), ("company_id", "=", False)], limit=1)
    if stage:
        vals = {}
        if is_default and not stage.is_default:
            vals["is_default"] = True
        if fold != bool(stage.fold):
            vals["fold"] = fold
        if stage.sequence != sequence:
            vals["sequence"] = sequence
        if vals:
            stage.write(vals)
        return stage
    return Stage.create(
        {
            "name": name,
            "sequence": sequence,
            "company_id": False,
            "is_default": bool(is_default),
            "fold": bool(fold),
        }
    )


def _run(env):
    stages = [
        ("筹备中", 5, True, False),
        ("在建", 10, False, False),
        ("停工", 20, False, False),
        ("竣工", 30, False, False),
        ("结算中", 40, False, False),
        ("保修期", 50, False, False),
        ("关闭", 60, False, True),
    ]
    default_found = env["project.project.stage"].sudo().search_count(
        [("is_default", "=", True), ("company_id", "=", False)]
    )
    for name, sequence, is_default, fold in stages:
        _ensure_stage(env, name, sequence, is_default=is_default and not default_found, fold=fold)


register(
    SeedStep(
        name="project_stages_min",
        description="Seed minimal project stages for base lifecycle usability.",
        run=_run,
    )
)
