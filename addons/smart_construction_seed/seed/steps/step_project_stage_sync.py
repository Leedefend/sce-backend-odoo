# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def run(env):
    Project = env["project.project"].sudo()
    Stage = env["project.project.stage"].sudo()
    updated = 0
    for project in Project.search([]):
        key = project._sc_compute_stage_key()
        stage = Project._get_stage_by_key(key)
        if stage and project.stage_id != stage:
            project.stage_id = stage.id
            updated += 1
    builtin_names = [
        "To Do",
        "In Progress",
        "Done",
        "Canceled",
        "Cancelled",
        "New",
    ]
    archived = 0
    for name in builtin_names:
        stages = Stage.search([("name", "ilike", name), ("active", "=", True)])
        if stages:
            archived += len(stages)
            stages.write({"active": False})
    env["ir.config_parameter"].sudo().set_param("sc.seed.project_stage_sync", str(updated))
    return {"ok": True, "updated": updated, "archived": archived}


register(
    SeedStep(
        name="project_stage_sync",
        description="Align project stage_id with lifecycle signals.",
        run=run,
    )
)
