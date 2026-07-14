# -*- coding: utf-8 -*-
"""Transactional sentinel proving fixture initialization preserves foreign data."""

import json

from odoo.addons.smart_construction_demo.tools.frontend_productization_fixture import ensure_fixture


def fail(message):
    print("[verify.frontend.fixture.nonfixture] FAIL %s" % message)
    raise SystemExit(2)


savepoint = env.cr.savepoint()
savepoint.__enter__()
try:
    pm = env["res.users"].sudo().search([("login", "=", "demo_role_pm")], limit=1)
    member = env["res.users"].sudo().search(
        [("login", "=", "demo_role_project_a_member")], limit=1
    )
    company = env["res.company"].sudo().search([("name", "=", "FE Company A")], limit=1)
    if not pm or not member or not company:
        fail("fixture principals are missing")

    project = env["project.project"].sudo().create(
        {
            "name": "NON-FIXTURE SENTINEL (transactional)",
            "company_id": company.id,
            "user_id": pm.id,
            "manager_id": pm.id,
        }
    )
    project.message_subscribe(partner_ids=[pm.partner_id.id, member.partner_id.id])
    task = env["project.task"].sudo().create(
        {"name": "NON-FIXTURE BUSINESS SENTINEL", "project_id": project.id}
    )

    def snapshot():
        current = env["project.project"].sudo().browse(project.id).exists()
        current_task = env["project.task"].sudo().browse(task.id).exists()
        followers = env["mail.followers"].sudo().search(
            [("res_model", "=", "project.project"), ("res_id", "=", project.id)]
        )
        return {
            "project_exists": bool(current),
            "user_id": current.user_id.id if current else False,
            "manager_id": current.manager_id.id if current else False,
            "follower_partner_ids": sorted(followers.mapped("partner_id").ids),
            "business_record": {
                "exists": bool(current_task),
                "project_id": current_task.project_id.id if current_task else False,
                "name": current_task.name if current_task else False,
            },
        }

    before = snapshot()
    ensure_fixture(env)
    after = snapshot()
    if before != after:
        fail("foreign project changed: before=%s after=%s" % (before, after))

    print("[verify.frontend.fixture.nonfixture] PASS")
    print(json.dumps({"db": env.cr.dbname, "before": before, "after": after}, ensure_ascii=False, indent=2))
finally:
    savepoint.__exit__(Exception, Exception("rollback sentinel"), None)
