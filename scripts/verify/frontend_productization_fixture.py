# -*- coding: utf-8 -*-
"""Read-only verification for the fixed frontend productization fixture."""

import json

from odoo.exceptions import AccessError


PASSWORD = "demo"
LOGINS = (
    "demo_role_finance",
    "demo_role_project_a_member",
    "demo_role_pm",
    "demo_role_owner",
)
MODELS = (
    "construction.contract",
    "sc.settlement.order",
    "payment.request",
    "sc.payment.execution",
)


def fail(message):
    print("[verify.frontend.fixture] FAIL %s" % message)
    raise SystemExit(2)


users = env["res.users"].sudo().search([("login", "in", list(LOGINS))])
by_login = {user.login: user for user in users}
missing = [login for login in LOGINS if login not in by_login]
if missing:
    fail("missing users: %s" % ",".join(missing))

login_results = {}
for login in LOGINS:
    uid = env["res.users"].sudo().authenticate(
        env.cr.dbname, login, PASSWORD, {"interactive": True}
    )
    login_results[login] = bool(uid)
if not all(login_results.values()):
    fail("one or more fixture users cannot authenticate")

companies = env["res.company"].sudo().search([("name", "in", ["FE Company A", "FE Company B"])])
company_by_name = {company.name: company for company in companies}
if set(company_by_name) != {"FE Company A", "FE Company B"}:
    fail("companies are missing or not unique")
for name in company_by_name:
    if env["res.company"].sudo().search_count([("name", "=", name)]) != 1:
        fail("company is not unique: %s" % name)

projects = env["project.project"].sudo().search(
    [("name", "in", ["FE Project A", "FE Project B", "FE Project C"])]
)
project_by_name = {project.name: project for project in projects}
if set(project_by_name) != {"FE Project A", "FE Project B", "FE Project C"}:
    fail("projects are missing or not unique")
for name in project_by_name:
    if env["project.project"].sudo().search_count([("name", "=", name)]) != 1:
        fail("project is not unique: %s" % name)

project_a = project_by_name["FE Project A"]
project_b = project_by_name["FE Project B"]
project_c = project_by_name["FE Project C"]
company_a = company_by_name["FE Company A"]
company_b = company_by_name["FE Company B"]
if project_a.company_id != company_a or project_b.company_id != company_a or project_c.company_id != company_b:
    fail("project/company matrix mismatch")

member = by_login["demo_role_project_a_member"]
member_env = env(user=member, context={**env.context, "allowed_company_ids": [company_a.id]})
member_projects = member_env["project.project"].search([("name", "like", "FE Project %")])
if member_projects.ids != project_a.ids:
    fail("project A member scope mismatch: %s" % member_projects.mapped("name"))

pm = by_login["demo_role_pm"]
pm_projects = env["project.project"].sudo().search(
    ["|", ("user_id", "=", pm.id), ("manager_id", "=", pm.id)]
)
if set(pm_projects.ids) != {project_a.id, project_b.id}:
    fail("PM assigned project scope mismatch: %s" % pm_projects.mapped("name"))
pm_followed_projects = env["project.project"].sudo().search(
    [("message_partner_ids", "in", [pm.partner_id.id])]
)
if set(pm_followed_projects.ids) != {project_a.id, project_b.id}:
    fail("PM followed project scope mismatch: %s" % pm_followed_projects.mapped("name"))

denied = []
for model_name in MODELS:
    model = member_env[model_name]
    visible = model.search([("project_id", "in", [project_a.id, project_b.id, project_c.id])])
    if not visible or set(visible.mapped("project_id").ids) != {project_a.id}:
        fail(
            "member visible scope mismatch for %s: %s"
            % (model_name, visible.mapped("project_id.name"))
        )
    for project in (project_b, project_c):
        target = env[model_name].sudo().search([("project_id", "=", project.id)], limit=1)
        if not target:
            fail("missing denied target for %s/%s" % (model_name, project.name))
        try:
            model.browse(target.id).read(["id"])
        except AccessError:
            denied.append("%s:%s" % (model_name, project.name))
        else:
            fail("member direct read unexpectedly allowed for %s/%s" % (model_name, project.name))

finance = by_login["demo_role_finance"]
finance_a = env(user=finance, context={**env.context, "allowed_company_ids": [company_a.id]})
finance_b = env(user=finance, context={**env.context, "allowed_company_ids": [company_b.id]})
requests_a = finance_a["payment.request"].search([("name", "like", "FE-%-PR-%")])
names_a = set(requests_a.mapped("name"))
if names_a != {"FE-A-PR-001", "FE-A-PR-002", "FE-B-PR-001"}:
    fail("finance company A scope mismatch: %s" % sorted(names_a))
requests_b = finance_b["payment.request"].search([("name", "like", "FE-%-PR-%")])
names_b = set(requests_b.mapped("name"))
if names_b != {"FE-C-PR-001"}:
    fail("finance company B scope mismatch or stale context: %s" % sorted(names_b))

for suffix, project in (("A", project_a), ("B", project_b), ("C", project_c)):
    contract = env["construction.contract"].sudo().search(
        [("subject", "=", "FE-%s Contract" % suffix)], limit=1
    )
    settlement = env["sc.settlement.order"].sudo().search(
        [("name", "=", "FE-%s-SET-001" % suffix)], limit=1
    )
    request = env["payment.request"].sudo().search(
        [("name", "=", "FE-%s-PR-001" % suffix)], limit=1
    )
    execution = env["sc.payment.execution"].sudo().search(
        [("name", "=", "FE-%s-PE-001" % suffix)], limit=1
    )
    if not all((contract, settlement, request, execution)):
        fail("incomplete business chain FE-%s" % suffix)
    if not (
        contract.project_id == project
        and settlement.project_id == project
        and settlement.contract_id == contract
        and request.project_id == project
        and request.contract_id == contract
        and request.settlement_id == settlement
        and execution.project_id == project
        and execution.contract_id == contract
        and execution.payment_request_id == request
    ):
        fail("business chain relation mismatch FE-%s" % suffix)

    expected_states = {
        "A": ("confirmed", "approve", "approved", "paid"),
        "B": ("draft", "draft", "draft", "draft"),
        "C": ("confirmed", "approve", "approved", "confirmed"),
    }[suffix]
    actual_states = (contract.state, settlement.state, request.state, execution.state)
    if actual_states != expected_states:
        fail("business chain state mismatch FE-%s: %s" % (suffix, actual_states))
    if request.amount != 1000.0 or execution.planned_amount != 1000.0:
        fail("same-amount company isolation fixture mismatch FE-%s" % suffix)

request_distribution = {
    suffix: env["payment.request"].sudo().search_count(
        [("project_id", "=", project.id), ("name", "like", "FE-%-PR-%")]
    )
    for suffix, project in (("A", project_a), ("B", project_b), ("C", project_c))
}
if request_distribution != {"A": 2, "B": 1, "C": 1}:
    fail("single/multi list fixture mismatch: %s" % request_distribution)
if env["payment.request"].sudo().search_count(
    [("name", "like", "FE-%-PR-%"), ("state", "=", "cancel")]
):
    fail("empty-state fixture mismatch: cancel filter must be empty")

counts = {
    "companies": env["res.company"].sudo().search_count([("name", "like", "FE Company %")]),
    "projects": env["project.project"].sudo().search_count([("name", "like", "FE Project %")]),
    "contracts": env["construction.contract"].sudo().search_count([("subject", "like", "FE-% Contract")]),
    "settlements": env["sc.settlement.order"].sudo().search_count([("name", "like", "FE-%-SET-001")]),
    "payment_requests": env["payment.request"].sudo().search_count([("name", "like", "FE-%-PR-%")]),
    "payment_executions": env["sc.payment.execution"].sudo().search_count([("name", "like", "FE-%-PE-001")]),
}
expected_counts = {
    "companies": 2,
    "projects": 3,
    "contracts": 3,
    "settlements": 3,
    "payment_requests": 4,
    "payment_executions": 3,
}
if counts != expected_counts:
    fail("fixed object counts mismatch: %s" % counts)

print("[verify.frontend.fixture] PASS")
print(json.dumps({
    "db": env.cr.dbname,
    "login_results": login_results,
    "counts": counts,
    "member_visible_projects": member_projects.mapped("name"),
    "member_direct_denials": denied,
    "pm_assigned_projects": pm_projects.mapped("name"),
    "pm_followed_projects": pm_followed_projects.mapped("name"),
    "finance_company_a_requests": sorted(names_a),
    "finance_company_b_requests": sorted(names_b),
    "relations": "consistent",
    "request_distribution": request_distribution,
    "empty_filter": "payment.request state=cancel",
}, ensure_ascii=False, indent=2))
