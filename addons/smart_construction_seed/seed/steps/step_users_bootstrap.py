# -*- coding: utf-8 -*-
import os

from odoo.exceptions import UserError

from ..registry import SeedStep, register


def _truthy(val):
    return str(val or "").lower() in ("1", "true", "yes", "y")


def _split_xmlids(raw):
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _resolve_groups(env, xmlids):
    if not xmlids:
        return []
    groups = []
    for xmlid in xmlids:
        rec = env.ref(xmlid, raise_if_not_found=False)
        if not rec:
            raise UserError(f"Bootstrap user group xmlid not found: {xmlid}")
        groups.append(rec)
    return groups


def _run(env):
    if not _truthy(os.getenv("SC_BOOTSTRAP_USERS")):
        return

    login = os.getenv("SC_BOOTSTRAP_ADMIN_LOGIN", "pm_admin").strip()
    password = os.getenv("SC_BOOTSTRAP_ADMIN_PASSWORD", "").strip()
    name = os.getenv("SC_BOOTSTRAP_ADMIN_NAME", "项目管理员").strip()
    update_password = _truthy(os.getenv("SC_BOOTSTRAP_UPDATE_PASSWORD"))
    company_mode = (os.getenv("SC_BOOTSTRAP_ADMIN_COMPANY_MODE") or "current").strip().lower()
    group_xmlids = _split_xmlids(
        os.getenv(
            "SC_BOOTSTRAP_ADMIN_GROUP_XMLIDS",
            "smart_construction_core.group_sc_role_project_manager",
        )
    )

    if not password:
        raise UserError("SC_BOOTSTRAP_ADMIN_PASSWORD is required when SC_BOOTSTRAP_USERS=1.")

    group_recs = _resolve_groups(env, group_xmlids)
    group_ids = [g.id for g in group_recs]

    Users = env["res.users"].sudo()
    user = Users.search([("login", "=", login)], limit=1)

    if company_mode == "all":
        companies = env["res.company"].sudo().search([])
        company_id = companies[:1].id if companies else env.company.id
        company_ids = companies.ids or [company_id]
    else:
        company_id = env.company.id
        company_ids = [company_id]

    vals = {
        "name": name,
        "login": login,
        "share": False,
        "company_id": company_id,
        "company_ids": [(6, 0, company_ids)],
    }
    if group_ids:
        vals["groups_id"] = [(6, 0, group_ids)]

    if user:
        if update_password:
            vals["password"] = password
        user.write(vals)
        return

    vals["password"] = password
    Users.create(vals)


register(
    SeedStep(
        name="users_bootstrap",
        description="Create or update bootstrap business admin user (opt-in).",
        run=_run,
    )
)
