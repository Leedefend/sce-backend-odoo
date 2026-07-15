from odoo.addons.smart_construction_core.services.payment_request_work_item_service import (
    PaymentRequestWorkItemService,
)
from odoo.exceptions import AccessError


def require(condition, message):
    if not condition:
        raise RuntimeError("[verify.frontend.my_work_approval.runtime] " + message)


def workspace(login, company=None):
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    require(user, "missing user %s" % login)
    scoped = env(user=user.id)
    if company:
        scoped = scoped(context={**scoped.context, "allowed_company_ids": [company.id]})
    return PaymentRequestWorkItemService(scoped, params={}, context=scoped.context).build()


company_a = env.ref("smart_construction_demo.fe_company_a")
company_b = env.ref("smart_construction_demo.fe_company_b")
finance_a = workspace("demo_role_finance", company_a)
finance_b = workspace("demo_role_finance", company_b)
executive = workspace("demo_role_executive", company_a)
member = workspace("demo_role_project_a_member", company_a)


class _RollbackProbe(Exception):
    pass


def create_probe(login):
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    scoped = env(user=user.id, context={**env.context, "allowed_company_ids": [company_a.id], "current_project_id": env.ref("smart_construction_demo.fe_project_a").id})
    project = scoped["project.project"].browse(env.ref("smart_construction_demo.fe_project_a").id)
    project_read = True
    try:
        project.check_access_rule("read")
        project.display_name
    except AccessError:
        project_read = False
    values = {
                "type": "pay",
                "business_category_id": env.ref("smart_construction_core.business_category_finance_payment_apply_pay").id,
                "project_id": project.id,
                "contract_id": env.ref("smart_construction_demo.fe_contract_a").id,
                "settlement_id": env.ref("smart_construction_demo.fe_journey_settlement_a").id,
                "partner_id": env.ref("smart_construction_demo.fe_partner_a").id,
                "currency_id": company_a.currency_id.id,
                "amount": 1.0,
                "state": "draft",
    }
    outcomes = {}
    for label, target in (("project_context", scoped), ("company_context", env(user=user.id, context={**env.context, "allowed_company_ids": [company_a.id]}))):
        created = False
        failure = ""
        try:
            with env.cr.savepoint():
                target["payment.request"].create(values)
                created = True
                raise _RollbackProbe()
        except _RollbackProbe:
            pass
        except Exception as exc:
            failure = type(exc).__name__
        outcomes[label] = {"created": created, "failure": failure}
    return {"payment_create_acl": bool(scoped["payment.request"].check_access_rights("create", raise_exception=False)), "project_read": project_read, **outcomes}


def names(result, key):
    section = next((row for row in result["sections"] if row["key"] == key), {"items": []})
    require(section.get("count") == len(section.get("items") or []), "%s count/list mismatch" % key)
    return {item["record"]["label"] for item in section.get("items") or []}


require(any("FE-JOURNEY-PAYMENT-001" in name for name in names(finance_a, "todo")), "finance draft todo missing")
require(any("FE-JOURNEY-PAYMENT-001" in name for name in names(finance_a, "initiated")), "finance initiated missing")
require(any("FE-JOURNEY-APPROVAL-001" in name for name in names(executive, "todo")), "executive approval todo missing")
require(any("FE-JOURNEY-REJECT-001" in name for name in names(executive, "todo")), "executive rejection todo missing")
require("FE-JOURNEY-PAYMENT-001" not in str(finance_b), "company B leaked company A work")
require("FE-JOURNEY-PAYMENT-001" not in str(member), "project member leaked payment work")
require("100.0" not in str(member), "project member leaked payment amount")
permission_matrix = {
    login: create_probe(login)
    for login in (
        "demo_role_finance",
        "demo_role_project_a_member",
        "demo_role_pm",
        "demo_role_owner",
        "demo_role_executive",
    )
}
print("[verify.frontend.my_work_approval.runtime] create_permission_matrix=%s" % permission_matrix)
print("[verify.frontend.my_work_approval.runtime] PASS")
