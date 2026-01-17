# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _normalize_demo_users(env, lang="zh_CN", tz="Asia/Shanghai"):
    Users = env["res.users"].sudo()
    users = Users.search(
        [
            ("share", "=", False),
            ("login", "not in", ["__system__", "public", "admin"]),
        ]
    )
    for user in users:
        vals = {}
        if lang and user.lang != lang:
            vals["lang"] = lang
        if tz and user.tz != tz:
            vals["tz"] = tz
        if vals:
            user.write(vals)


def _run(env):
    _normalize_demo_users(env)


register(
    SeedStep(
        name="demo_user_prefs",
        description="Normalize demo users' lang/tz for consistent UX.",
        run=_run,
    )
)
