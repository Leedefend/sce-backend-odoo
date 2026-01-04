# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _run(env):
    """
    Ensure demo projects have a real owner (demo_pm) instead of __system__/null.
    Safe to re-run (idempotent).
    """
    Users = env["res.users"].sudo()
    Projects = env["project.project"].sudo()

    demo_pm = Users.search([("login", "=", "demo_pm")], limit=1)
    if not demo_pm:
        return {"skipped": True, "reason": "demo_pm not found"}

    # include inactive user (__system__ is usually inactive in demo DB)
    sys_user = Users.with_context(active_test=False).search(
        [("login", "=", "__system__")], limit=1
    )
    sys_uid = sys_user.id if sys_user else False

    domain = ["|", ("user_id", "=", False), ("user_id", "=", sys_uid)] if sys_uid else [("user_id", "=", False)]
    targets = Projects.search(domain)

    if not targets:
        return {"ok": True, "updated": 0}

    targets.write({"user_id": demo_pm.id})
    return {"ok": True, "updated": len(targets), "user_id": demo_pm.id}


register(
    SeedStep(
        name="project_owner_demo_pm",
        description="Assign demo project owner to demo_pm when missing/system.",
        run=_run,
    )
)
