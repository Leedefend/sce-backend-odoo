# -*- coding: utf-8 -*-
from ..registry import SeedStep, register


def _resolve_lang(env, preferred="zh_CN", fallback="en_US"):
    Lang = env["res.lang"].sudo().with_context(active_test=False)
    for code in [preferred, fallback]:
        if not code:
            continue
        lang = Lang.search([("code", "=", code)], limit=1)
        if not lang:
            continue
        if not lang.active:
            lang.write({"active": True})
        return lang.code
    lang = Lang.search([("active", "=", True)], limit=1)
    if lang:
        return lang.code
    return False


def _normalize_demo_users(env, lang="zh_CN", tz="Asia/Shanghai"):
    resolved_lang = _resolve_lang(env, preferred=lang)
    Users = env["res.users"].sudo()
    users = Users.search(
        [
            ("share", "=", False),
            ("login", "not in", ["__system__", "public", "admin"]),
        ]
    )
    for user in users:
        vals = {}
        if resolved_lang and user.lang != resolved_lang:
            vals["lang"] = resolved_lang
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
