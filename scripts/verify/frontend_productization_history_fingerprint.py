# -*- coding: utf-8 -*-
"""Read-only fingerprint for proving a rejected fixture call left sc_demo intact."""

import json


counts = {
    "users": env["res.users"].sudo().search_count([]),
    "companies": env["res.company"].sudo().search_count([]),
    "projects": env["project.project"].sudo().search_count([]),
    "contracts": env["construction.contract"].sudo().search_count([]),
    "settlements": env["sc.settlement.order"].sudo().search_count([]),
    "payment_requests": env["payment.request"].sudo().search_count([]),
    "payment_executions": env["sc.payment.execution"].sudo().search_count([]),
}
module = env["ir.module.module"].sudo().search([("name", "=", "smart_construction_demo")], limit=1)
payload = {
    "db": env.cr.dbname,
    "demo_module_state": module.state if module else "absent",
    "counts": counts,
    "project_user_links": env["project.project"].sudo().search_count([("user_id", "!=", False)]),
    "project_manager_links": env["project.project"].sudo().search_count([("manager_id", "!=", False)]),
    "project_followers": env["mail.followers"].sudo().search_count([("res_model", "=", "project.project")]),
}
print("FRONTEND_HISTORY_FINGERPRINT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
